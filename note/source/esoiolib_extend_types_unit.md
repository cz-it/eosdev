# EOS 货币标量和单位制

如果手动转过账，转EOS的话，在填数目的时候一般是"10.0000 EOS"或者如果最近玩过PRA 糖果的话，查询记录应该有类似"7.0000 EPRA"这样
类似的字眼。从字面意思也可以猜到，前面的数字表示数量，后面的字母表示单位，这个就是EOS的货币标量和单位制。

如果要在内部对这样的标量进行计算，前面数字好说，加减就可以。那么后面的字符串改怎么办呢？另外这个标量的精确度要如何表示呢？

eosiolib给出的答案是"symbol"和"asset"：将字符串转换成数字并将精确度记录在其中。

## symbol 定义

先来看symbol的定义：

    typedef uint64_t symbol_name;

    struct symbol_type {

      symbol_name value;
      ...
    }

其实symbol本质就是个uint64。

    EOSLIB_SERIALIZE( symbol_type, (value) )

在结构体的最后有这样的宏，这里表示会对value做变长序列化造作。序列化参见另一篇专门讨论的[部分]();

## symbol操作方法

上面说了"EOS"是字符串，那他是怎么放到一个uint64里面去的呢？

### 转换精髓

symbol定义了个转换函数：

     static constexpr uint64_t string_to_symbol( uint8_t precision, const char* str ) {
        uint32_t len = 0;
        while( str[len] ) ++len;

        uint64_t result = 0;
        for( uint32_t i = 0; i < len; ++i ) {
           if( str[i] < 'A' || str[i] > 'Z' ) {
              /// ERRORS?
           } else {
              result |= (uint64_t(str[i]) << (8*(1+i)));
           }
        }

        result |= uint64_t(precision);
        return result;
     }

这个函数传入一个表示精度的"precision"和一个字符串表示单位 "str"。上面的逻辑就是：

    将字符串每个字母的ASCII码从低位到高位依次放入十进制位上，然后最低位放进度信息。

为了方便 ， 合约中我们可以使用宏：

     #define S(P,X) ::eosio::string_to_symbol(P,#X)

### 货币合法单位

这里单位值也不是随便定义的，我们知道账户名是".1-5a-z"。货币单位的合法值则是"A-Z":

     static constexpr bool is_valid_symbol( symbol_name sym ) {
        sym >>= 8; /// skip precision
        for( int i = 0; i < 7; ++i ) {
           char c = (char)(sym & 0xff);
           if( !('A' <= c && c <= 'Z')  ) return false;
           sym >>= 8;
           if( !(sym & 0xff) ) {
              do {
                sym >>= 8;
                if( (sym & 0xff) ) return false;
                ++i;
              } while( i < 7 );
           }
        }
        return true;
     }

有了上面的转换算法，只要将ASCII转换会字符并判断是否在 "A-Z"就可以了。

同样的基于这个算法也可以得到单位字符的长度、打印对应的字符等，这里不再赘述。分别调用的是下面两个函数：

    uint32_t name_length()const
    void print(bool show_precision=true)const


## asset

asset定义为：

    struct asset {

          int64_t      amount;

          symbol_type  symbol;
    ...
    }

看过前面的描述。应该知道这里"symbol_type"就是个"uint64"。所以总的来说：
asset就是两个64bit的整形。

从字面意思可以看到，这个数据结构主要就存两个东西：

* 数目： amount
* 单位：symbol

symbol的定义参见 上面定义。只有一个数目，感觉基本就没的说了。。。。

    EOSLIB_SERIALIZE( asset, (amount)(symbol) )

在结构体的最后有这样的宏，这里表示会对amount和symbol做变长序列化造作。序列化参见另一篇专门讨论的[部分]();

## 函数实现

这里我们还是结合代码看下，对于金融相关，尤其涉及数字的，边界检查需要特别注意。

### 构造函数

      explicit asset( int64_t a = 0, symbol_type s = CORE_SYMBOL )
      :amount(a),symbol{s}
      {
         eosio_assert( is_amount_within_range(), "magnitude of asset amount must be less than 2^62" );
         eosio_assert( symbol.is_valid(),        "invalid symbol name" );
      }

构造函数里面直接带上assert,CPP里面是非常的不常见。。。。

不过我们知道因为WebAssembly的runtime存在，这里的assert不会真正引起crash。只是一个检查。这里可以看到ammount的上限是2^62。那么当我们的合约再接受
转账的时候也应该检查这个范围才对。

### accesser

既然是存数据的，想象其他编程语言如C#/Typescript都会有个属性访问器，在这里我们可以做边际检查：

      void set_amount( int64_t a ) {
         amount = a;
         eosio_assert( is_amount_within_range(), "magnitude of asset amount must be less than 2^62" );
      }

这里set会检查是否在合法范围。

### 加减乘除

和定点实现的浮点数一样，计量单位肯定需要常用的计算，如加减乘除。

这里只看一个减法，感受下在每个数据可能到达边际时候的处理：

      asset& operator-=( const asset& a ) {
         eosio_assert( a.symbol == symbol, "attempt to subtract asset with different symbol" );
         amount -= a.amount;
         eosio_assert( -max_amount <= amount, "subtraction underflow" );
         eosio_assert( amount <= max_amount,  "subtraction overflow" );
         return *this;
      }

每次操作后设计修改asset.amount都需要做范围判断。

其他都是类似的操作符重载，不在赘述。

### 大小比较

和定点实现的浮点数一样，计量单位也需要大小比较：

      friend bool operator<=( const asset& a, const asset& b ) {
         eosio_assert( a.symbol == b.symbol, "comparison of assets with different symbols is not allowed" );
         return a.amount <= b.amount;
      }

在比较前，首先判断比较的两个asset的单位symbol是否一样，一样的前提下才能比较amount。  

## 总结

asset和symbol共同组成了EOS的货币标量和单位制。symbol用来表示不同的货币，asset则定义了数量和运算。在合约代码中对asset的操作是最基本也是
最常用的操作。
