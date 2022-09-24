### How to do things

*  How to create topic in kafka
```bash
./kafka-topics.sh --create --topic davinder.test --partitions 3 --bootstrap-server localhost:9092
```

*  how to create dummy data in kafka
```bash
./kafka-producer-perf-test.sh --topic davinder.test --num-records 200000 --record-size 10 --producer-props bootstrap.servers=localhost:9092 --throughput 1000
```