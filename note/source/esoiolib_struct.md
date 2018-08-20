# eosiolib基本类型
EOS为了方便大家做合约开发，提供了一个SDK库:eosiolib。在代码路径：eos/contruct/eosiolib目录下可以找到。

eosiolib定义了一系列的基本类型和扩张类型，方便大家来实现合约。

## 数值基本类型
int基本类型有：

类型名|类型|说明
---|---|---
account_name | uint64_t | 账号名
permission_name | uint64_t | 权限名
table_name | uint64_t | 表名
time | uint32_t | 时间，单位为秒
scope_name | uint64_t | 域名，一般指一个合约
action_name | uint64_t | action的名子
weight_type | uint16_t | 权限权重值


## 复合基本类型
所有复合基础类型都是两字节对齐。

    #define ALIGNED(X) __attribute__ ((aligned (16))) X

这里运用了LLVM集成GNU的关键字`__attribute__`和方法`aligned`，功能可以参考ANSI C的`pack`。比如这里：

    struct ALIGNED(checksum256) {
       uint8_t hash[32];
    };

其实和：

    #pragma pack(2)
    struct checksum256 {
        uint8_t hash[32];
    };    

作用一致。    

类型名|类型|说明
---|---|---
 public_key | 34 bytes | 公钥 
 signature | 66 bytes | 签名 
 checksum256 | 256-bit | 256位检验和 
 checksum160 | 160-bit | 160位校验和 
 checksum512 | 512-bit | 512位校验和 
 transaction_id_type | checksum256 | transaction的ID 
 block_id_type | checksum256 | block的ID 

 ## C++ 扩展类型
 CPP在上面基础类型之上扩展了一个"name"的类型

    struct name {    

        account_name value = 0;
    }

其本质就是个"account_name"或者说是 "uint64_t"。

而要如何比较方便的记录名字，我们知道EOS的地址是一个字符串，其在内部表示实际上就是这里的uint64。因此eosiolib提供了字符串到name（uint64)的
转换函数：

       static constexpr uint64_t string_to_name( const char* str ) {

          uint32_t len = 0;
          while( str[len] ) ++len;

          uint64_t value = 0;

          for( uint32_t i = 0; i <= 12; ++i ) {
             uint64_t c = 0;
             if( i < len && i <= 12 ) c = uint64_t(char_to_symbol( str[i] ));

             if( i < 12 ) {
                c &= 0x1f;
                c <<= 64-5*(i+1);
             }
             else {
                c &= 0x0f;
             }

             value |= c;
          }

          return value;
       }

其本质就是取字符串中每个字母的ASCII对应的4bit的数字，然后将其往高位挪，直到计算完所有的字符。

在合约里面，我们经常看到类似：

    N("eosio.token")

这样代码，实际上就是讲合约名称转换成对应的name:

     #define N(X) ::eosio::string_to_name(#X)    

其宏定义就是调用了上面的   string_to_name。  

通过该函数的"to_string"函数可以将其转换成对应的字符串字面值：

      std::string to_string() const {
         static const char* charmap = ".12345abcdefghijklmnopqrstuvwxyz";

         std::string str(13,'.');

         uint64_t tmp = value;
         for( uint32_t i = 0; i <= 12; ++i ) {
            char c = charmap[tmp & (i == 0 ? 0x0f : 0x1f)];
            str[12-i] = c;
            tmp >>= (i == 0 ? 4 : 5);
         }

         trim_right_dots( str );
         return str;
      }

这里就是对`string_to_name`的一个逆运算：从高位往地位取每4bit获得其对应的ascii表示的字符，将字符连接起来。