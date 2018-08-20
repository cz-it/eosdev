# eosiolib扩展类型: Asset

EOS为了方便大家做合约开发，提供了一个SDK库:eosiolib。在代码路径：eos/contruct/eosiolib目录下可以找到。

eosiolib定义了一系列的基本类型和扩张类型，方便大家来实现合约。

如果看过一些合约代码（比如官方例子）或者一些ABI的话，对"asset"这个类型一定不陌生。一般他的值是"100.0000 EOS"这样类似的，这里表示100个EOS
（PS: 好多钱）。

这个传入的是一个字符串，那如何做加钱、减钱的逻辑呢？这个字符串是如何在合约中被使用呢？

答案就在"asset"这个结构里面。

## asset

asset定义为：

    struct asset {

          int64_t      amount;

          symbol_type  symbol;
    ...
    }

看过前面的[《eosiolib扩展类型: Symbol](https://www.jianshu.com/p/755296ce6846)。应该知道这里"symbol_type"就是个"uint64"。所以总的来说：
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
