# Construct代码研读

## 1. 关键数据结构
###  symbol 
symbol 本质就是uint64,然后用低8bit来表示这个货币符号的精度，一般为4。如100.0000 EOS。

###  asset
本质就是做了运算约束的带单位（sybmle）的数据类型。单位就是什么EOS、SYS等。本身支持加减乘除
等基本运算（同币种)。

### XXX name

* account_name
* permission_name
* table_name
* scope_name
* action_name

实际上就是uint64的typdef

而类似：

* public_key
* signature
* checksum256
* checksum160
* checksum512
* transaction_id_type
* block_id_type

则是uint8[]字符数组


## 2.工具函数

### 时间
* current_time: 当前时间戳，单位ms。Unix时间
* now: 当前时间戳，单位s。类似time(NULL)
