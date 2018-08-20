# 日志打印 - print.h
EOS智能合约的开发，目前还没有办法像传统CPP开发一样通过lldb/gdb进行断点调试。目前只有通过
打日志的方式进行调试。若想在命令行中将合约日志打印出来，需要在启动nodeos的时候传入`--contracts-console`
选项，否则日志不会被打印。

## 基本C函数
在print.h文件中，提供了几个基本的C函数，因为C没有重载，所以其实可以认为是提供了print的统一桥接层。
这里为什么说是桥接层呢？ 如果观察"eosiolib"目录的代码，大家会发现，这里大部分是函数的声明，而没有
实现，比如这里的print就没有找到的他的实现。

实际上print的实现下eos的代码的"libraries/chain/wasm_interface.cpp"这个文件中：

    class console_api : public context_aware_api {
       public:
          console_api( apply_context& ctx )
          : context_aware_api(ctx,true)
          , ignore(!ctx.control.contracts_console()) {}

          // Kept as intrinsic rather than implementing on WASM side (using prints_l and strlen) because strlen is faster on native side.
          void prints(null_terminated_ptr str) {
             if ( !ignore ) {
                context.console_append<const char*>(str);
             }
          }
    ...
    }


那懂CPP的肯定会说，这里是C++啊，还是个类，怎么能说是上面的C的实现呢？

原因是，其实我们的合约C++代码最终是要编译成WebAssembly代码，而WebAssembly在每个节点上执行的时候实际上是跑在一个runtime中，可以认为其
是一个沙盒或者说是虚拟机。这样在类比如Java里面的JNI(做Android开发的同学一定不陌生),或者JSBridge（做移动端开发的东西一定知道），从其他
语言调用C/C++，其接口层一般都是通过C类进行桥接的，因为其本质就是找到函数的代码段地址并执行，相对容易且稳定。

在上面的这个文件中：

    REGISTER_INTRINSICS(console_api,
       (prints,                void(int)      )
       (prints_l,              void(int, int) )
       (printi,                void(int64_t)  )
       (printui,               void(int64_t)  )
       (printi128,             void(int)      )
       (printui128,            void(int)      )
       (printsf,               void(float)    )
       (printdf,               void(double)   )
       (printqf,               void(int)      )
       (printn,                void(int64_t)  )
       (printhex,              void(int, int) )
    );

实现了对相关桥接调用的注册。

在上面的实现中，我们可以看到，print本质就是通过`context.console_append<const char*>(str)`将内容打印到控制台日志上。

这里来看pirnt.h提供的几个打印函数：

 函数原型 | 作用 
 --- | --- 
 void prints( const char* cstr ); | 打印char *字符串 
 void prints_l( const char* cstr, uint32_t len); | 打印char *字符串中指定的长度 
 void printi( int64_t value ); | 打印int64 
 void printui( uint64_t value ); | 打印uint64 
 void printi128( const int128_t* value ); | 打印int128 
 void printui128( const uint128_t* value ); | 打印uint128 
 void printsf(float value); | 打印32位的float 
 void printdf(double value); | 打印double 
 void printqf(const long double* value); | 打印long double 
 void printn( uint64_t name ); | 将一个uint64按照base32打印字符串内容 
 void printhex( const void* data, uint32_t datalen ); | 将二进制内容按照hex编码打印 

## C++扩展

因为我们写合约一般是按照CPP来写的。所以eosiolib又为我们封装了一层CPP接口。比如上面的printxx都封装到了print这个函数中。这里只看一个实现：

    inline void print( const char* ptr ) {
        prints(ptr);
    }

这里重复利用了CPP重载函数的特性。

除了print函数，CPP的接口还提供了类似printf/cout这样的便利封装,比如：

    inline void print( bool val ) {
        prints(val?"true":"false");
    }

打印bool值的字符串表示。


    template<typename T>
    inline void print( T&& t ) {
        t.print();
    }

通过模板来实现对类型print函数的调用。

以及牛逼的：

    inline void print_f( const char* s ) {
        prints(s);
    }

    template <typename Arg, typename... Args>
    inline void print_f( const char* s, Arg val, Args... rest ) {
        while ( *s != '\0' ) {
            if ( *s == '%' ) {
                print( val );
                print_f( s+1, rest... );
                return;
            }
         prints_l( s, 1 );
         s++;
        }
    }  

这里通过模板实现了printf格式化输出的功能。可以像使用C里面的`printf`一样使用 `print_f`

如果你用过JavaScript的话，肯定会记得通过`console.log(a,b,c)`就可以把三个变量依次打印出来。这里CPP的接口也提供了类似的功能：

    template<typename Arg, typename... Args>
    void print( Arg&& a, Args&&... args ) {
         print(std::forward<Arg>(a));
         print(std::forward<Args>(args)...);
    }

通过传递不定参数给print即可将他们都打印出来。

## 总结
EOS 合约开发目前只能通过打日志的方式来进行逻辑的测试和调试，因为需要给nodeos启动的时候传递选项，那么就需要有自己的测试节点环境（环境部署可以参考
之前的[教程](https://www.jianshu.com/p/65e9057d2d85)）。日志打印通过print系列函数，其CPP接口已经相当友好。基本通过`print` `print_f`
可以满足日常的调试需求。