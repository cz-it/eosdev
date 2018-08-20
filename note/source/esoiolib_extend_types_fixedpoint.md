# eosiolib扩展类型: FixedPoint
EOS为了方便大家做合约开发，提供了一个SDK库:eosiolib。在代码路径：eos/contruct/eosiolib目录下可以找到。

eosiolib定义了一系列的基本类型和扩张类型，方便大家来实现合约。

>   /**
>    * @defgroup fixedpoint Fixed Point
>    * @ingroup mathcppapi
>    * @brief 32,64,128,256 bits version of fixed point variables
>    *
>    * Floating point operations are indeterministic, hence is prevented in smart contract.
>    * The smart contract developers should use the appropriate Fixed_Point template class
>    * by passing the number to be represented in integer format and the number of decimals
>    * required.
>    * These template classes also support the arithmetic operations and basic comparison operators
>    * @{
>    */

这段是来自文件"fixedpoint.hpp"里面的注释，意思是说在合约里面因为浮点预算的不确定性，所以合约是不支持使用浮点数的，所有的
浮点数运算都要通过定点数来进行。为此eosiolib提供了32位、64位、128位以及256位（当前还不支持，后续会支持）整形表示的浮点数。

其本质就是拿uint32/64/128里面的低位作为整数部分，高位作为小数部分。那么整数和小数部分的分割点在哪里呢？且看定义：

    template <uint8_t Q> struct fixed_point32;
    template <uint8_t Q> struct fixed_point64;
    template <uint8_t Q> struct fixed_point128;

通过模板<uint8_t Q>  Q来表示有几位小数。比如：

    fixed_point128<6> a(123232.455667233)   // 会整数"123232" + 小数 ".455667"
    fixed_point64<3> a(1234.455667)         // 会整数"1234" + 小数 ".455"



## fixed_point 接口
有了数据结构来存储相应的数据后，要如何方便的操作他们呢？这里 eosiolib的CPP接口实现提供了若干接口来使得其和操作普通的float一样
方便。

一般的float操作包含赋值、比较、加减乘除、获取整数、获取小数等操作。

赋值操作可以直接在三个类型低到高直接转换：

    fixed_point128 a;
    fixed_point64 b;
    fixed_point32 c;

    a=b; // ok
    a=c; // ok
    c=b; // wrong

32位和64可以支持完整的加减乘除运行，因为有低位到高位的转换，所以32位也可以和64位进行运算。128位暂不支持四则运算。

    fixed_point128 m;
    fixed_point64 b;
    fixed_point64 ba;
    fixed_point64 bc;
    fixed_point32 c;

    b = ba+bc; //ok
    b = ba+c ; //ok c会转换成fixed_point64
    m = b*bc;  // ok c会转换成fixed_point64相乘得到fixed_point128类型

所有类型都能比较运行。

    fixed_point128<6> a(123232.455667233)   
    fixed_point64<3> b(1234.455667)  

    a>b ; // true

## fixed_point实现

以下代码拿fixed_point128作为示例，一则学习接口使用，二则学习期实现。

    template <uint8_t Q>
    struct fixed_point128
    {
        static_assert(Q < 128, "Maximum number of decimals supported in fixed_point128 is 128 decimals");

        /**
         * @brief Value of the fixed point represented as int128_t
         * 
         * Value of the fixed point represented as int128_t
         */
        int128_t val;
        ...
    }

fixed_point128本质就是一个128bit的内存单元，用来存储一个128bit的二进制内容。

来看下如何获得浮点数的整形部分，根据之前的理解，只要取出来其低（128-Q)位就是我们需要的整数部分了：

        int128_t int_part() const {
            return val >> Q;
        }

这里通过移位进行实现。

那么同样的，只要取出其高Q位即可得到小数部分：

        uint128_t frac_part() const {
            if(!Q) return 0;
            return uint128_t(val << (32-Q));
        } 

除此之外，fixed_point128还定义了fixed_point64/fixed_point32的转换以及比较运行符的重载：

        // 转换声明
        template <uint8_t qr> fixed_point128 &operator=(const fixed_point32<qr> &r);

        template <uint8_t qr> fixed_point128 &operator=(const fixed_point64<qr> &r);

        template <uint8_t qr> fixed_point128 &operator=(const fixed_point128<qr> &r);

        // 转换实现

        template<uint8_t Q> template<uint8_t QR>
        fixed_point128<Q>::fixed_point128(const fixed_point128<QR> &r) {
            val = assignHelper<int128_t>(r.val, Q, QR);
        }

        template<uint8_t Q> template<uint8_t QR>
        fixed_point128<Q>::fixed_point128(const fixed_point64<QR> &r) {
            val = assignHelper<int128_t>(r.val, Q, QR);
        }

        template<uint8_t Q> template <uint8_t QR>
        fixed_point128<Q>::fixed_point128(const fixed_point32<QR> &r) {
            val = assignHelper<int128_t>(r.val, Q, QR);
        }


        // 比较运算的声明和实现
        template <uint8_t qr> bool operator==(const fixed_point128<qr> &r) { return (val == r.val);}

        template <uint8_t qr> bool operator>(const fixed_point128<qr> &r) { return (val > r.val);}

        template <uint8_t qr> bool operator<(const fixed_point128<qr> &r) { return (val < r.val);}   

这里主要就是对运算符的重载实现，其中转换中使用的`assignHelper`为：

    template<typename T>
    T assignHelper(T rhs_val, uint8_t q, uint8_t qr)
    {
        T result = (q > qr) ? rhs_val << (q-qr) : rhs_val >> (qr-q);
        return result;
    }

这里就是先判断谁的精度高，如果赋值给fixed_point128的精度低，那么就将要赋予的值左移补充小数位。否则就右移舍去高出的整数部分。

既然是表示的浮点数，那么肯定也要支持常用的浮点运行，比如加减乘除：

    // 加法运行
    template<uint8_t Q> template<uint8_t QR>
    fixed_point64< (Q>QR)?Q:QR > fixed_point64<Q>::operator+(const fixed_point64<QR> &rhs) const
    {
        // 如果精度一致，进行普通加减即可
        if(Q == QR)
        {
            return fixed_point64<Q>(val + rhs.val);
        }
        // 精度不一致取较大者进行运算
        return fixed_point64<(Q>QR)?Q:QR>(
            fixed_point64<(Q>QR)?Q:QR>( *this ).val +
            fixed_point64<(Q>QR)?Q:QR>( rhs ).val
        );
    }

    // 减法运算
    template<uint8_t Q> template<uint8_t QR>
    fixed_point64< (Q>QR)?Q:QR > fixed_point64<Q>::operator-(const fixed_point64<QR> &rhs) const
    {
        // 如果精度一致，进行普通加减即可
        if(Q == QR)
        {
            return fixed_point64<Q>(val - rhs.val);
        }
        // 精度不一致取较大者进行运算
        return fixed_point64<(Q>QR)?Q:QR>(
            fixed_point64<(Q>QR)?Q:QR>( *this ).val -
            fixed_point64<(Q>QR)?Q:QR>( rhs ).val
        );
    }

    // 乘法运算
    template<uint8_t Q> template <uint8_t QR>
    fixed_point128<Q+QR> fixed_point64<Q>::operator*(const fixed_point64<QR> &r) const {
        // 乘法需要更大的位去保存
        return fixed_point128<Q+QR>(int128_t(val)*r.val);
    }

    // 除法运算
    template <uint8_t Q> template <uint8_t QR>
    fixed_point128<Q+64-QR> fixed_point64<Q>::operator/(const fixed_point64<QR> &r) const {
        //除法按照公式 Q(X+64-Y) = Q(X+64) / Q(Y) 来进行计算
       eosio_assert( !(r.int_part() == 0 && r.frac_part() == 0), "divide by zero" );
        return fixed_point128<Q+64-QR>((int128_t(val)<<64)/r.val);
    }

目前64位和32位提供了上面四种计算，因为256还没有支持，所以128位的乘法、除法没法实现，对应加法减法也未进行实现。

## 总结

上面的内容阐释了怎么将一个浮点数用整形来表示并进行比较、加减乘除、复制转换等一个浮点数该有的运行。通过这个内容就可以理解之前分析的
"剪影"/"ITE"里面的数值为啥是那么大了，比普通单位大了10000倍，那是因为其将这4位做为了小数。
