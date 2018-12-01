# eosiolib扩展类型: Time

> The EOS.IO software introduces a new blockchain architecture designed to enable vertical and horizontal scaling of decentralized applications. This is achieved by creating an operating system-like construct upon which applications can be built.

EOS的白皮书中说他要打造一个类似操作系统的分布式系统。而我们合约就好比运行在操作系统上的软件。那么我们在写程序
软件的时候，最常用的时间元素是怎样的呢？

来看eosiolib 里面的time.hpp。


## 获取时间
在看time.hpp之前需要先看下"system.h"这个文件。这个文件里面定义两个获取时间的函数：

    uint64_t  current_time();

    /**
    *  Returns the time in seconds from 1970 of the block including this action
    *  @brief Get time (rounded down to the nearest second) of the current block (i.e. the block including this action)
    *  @return time in seconds from 1970 of the current block
    */
    uint32_t  now() {
      return (uint32_t)( current_time() / 1000000 );
    }

用来获得当前的时间戳（从1970 Unix纪元时间到现在的过去的时间）。前者单位为毫秒而后者单位为秒。

## 时间单位表示
上面获得的时间是以uint64和uint32来表示的整形，看过前面的讨论的浮点和货币单位的文章的话，自然会想到这里需要一个统一量来表示时间，否则进行时间计算时
就会变的非常复杂。而 在EOS系统内部 是通过time_point"表示毫秒，"time_point_sec"表示秒。

### microseconds

先来看个定义：

    class microseconds {

        int64_t _count;
        EOSLIB_SERIALIZE( microseconds, (_count) )
    }

毫秒实际上就是个int64。只是这个int64做了n个操作符的重载来实现其时间的计算，重载的运算符和int64本身的并没有什么区别。唯一增加的就是提供了到秒的转换：

        int64_t to_seconds()const { return _count/1000000; }  


### time_point
在来看类：

      class time_point {
              microseconds elapsed;
            EOSLIB_SERIALIZE( time_point, (elapsed) )
      };          

则可以认为是毫秒的重定义。在EOS合约里如果用到毫秒一般会用这个类，本质上也是个int64。但是比 microseconds 多出了：

        const microseconds& time_since_epoch()const { return elapsed; }
        uint32_t            sec_since_epoch()const  { return uint32_t(elapsed.count() / 1000000); }

来获取上面说的Unit纪元时间。

另外就是有个从标准字符串转换时间的工具：

        operator std::string()const;
        static time_point from_iso_string( const std::string& s );  

在[ISO-8601](https://www.iso.org/iso-8601-date-and-time-format.html)中规定了统一的时间字符串格式。类似：

    "2009-W01-1"
    2007-03-01T13:00:00Z/2008-05-11T15:30:00Z
    P1Y2M10DT2H30M/2008-05-11T15:30:00Z

等，在Block我们常见到的有"2018-08-21T11:31:36.000"。所以在cloes命令中如果需要传递时间的时候，一般就会用到这个格式。    

### time_point_sec
从字面意思也可以推导出：time_point_sec是time_point表示秒的结构：

    class time_point_sec
    {
        uint32_t utc_seconds;

        EOSLIB_SERIALIZE( time_point_sec, (utc_seconds) )
    }；

### 运算操作

除了上面的定义外这两个time_point 主要定义了互相之间的运算操作。这样就不用我们手动的去*1000或者/1000了。

    //time_point
        time_point&  operator += ( const microseconds& m)                           { elapsed+=m; return *this;                 }
        time_point&  operator -= ( const microseconds& m)                           { elapsed-=m; return *this;                 }
        time_point   operator + (const microseconds& m) const { return time_point(elapsed+m); }
        time_point   operator + (const time_point& m) const { return time_point(elapsed+m.elapsed); }
        time_point   operator - (const microseconds& m) const { return time_point(elapsed-m); }
        microseconds operator - (const time_point& m) const { return microseconds(elapsed.count() - m.elapsed.count()); }

    //time_point_sec
        friend time_point   operator + ( const time_point_sec& t, const microseconds& m )   { return time_point(t) + m;             }
        friend time_point   operator - ( const time_point_sec& t, const microseconds& m )   { return time_point(t) - m;             }
        friend microseconds operator - ( const time_point_sec& t, const time_point_sec& m ) { return time_point(t) - time_point(m); }
        friend microseconds operator - ( const time_point& t, const time_point_sec& m ) { return time_point(t) - time_point(m); }

两块函数在加上类型之间的转换，就实现了三个数据类型之间的加减操作了。


### block_timestamp

除了上面的时间。我们知道block信息查询的时候有个时间，因为block是500ms固定产生的，所以block的idx也就表征了时间。因此又定义了block时间：

    class block_timestamp {
        public:
            uint32_t slot;
            static constexpr int32_t block_interval_ms = 500;
            static constexpr int64_t block_timestamp_epoch = 946684800000ll;  // epoch is year 2000

            EOSLIB_SERIALIZE( block_timestamp, (slot) )
    }  

实际上就是当前是从Unix纪元时间来算的话，第多少个block。

## 总结

EOS将时间单位进行了统一：

* 毫秒：time_point
* 秒：  time_point_sec

并通过类型转换和运算符重载实现了不同单位之间的运算，而ABI里面定义的时间则为标准的ISO格式字符串。这样就可以实现通过cleos传递时间，并在合约中进行计算这样的过程。      