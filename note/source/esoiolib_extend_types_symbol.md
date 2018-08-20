# eosiolib扩展类型: Symbol
EOS为了方便大家做合约开发，提供了一个SDK库:eosiolib。在代码路径：eos/contruct/eosiolib目录下可以找到。

eosiolib定义了一系列的基本类型和扩张类型，方便大家来实现合约。

如果手动转过账，转EOS的话，在填数目的时候一般是"10.0000 EOS"或者如果最近玩过PRA 糖果的话，查询记录应该有类似"7.0000 EPRA"这样
类似的字眼。从字面意思也可以猜到，前面的数字表示数量，后面的字母表示单位。

如果要在内部对这样的标量进行计算，前面数字好说，加减就可以。那么后面的字符串改怎么办呢？另外这个标量的精确度要如何表示呢？

eosiolib给出的答案是"symbol"：将字符串转换成数字并将精确度记录在其中。

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

### 火币合法单位

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
