package com.binance.loadgen;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.common.serialization.StringSerializer;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Synthetic trade generator for load-testing the pipeline.
 *
 * Uses one shared KafkaProducer with N worker threads (one per symbol).
 * Rate limiting uses a lag-compensating approach: each thread tracks how
 * many messages it *should* have sent and sleeps only when it is ahead.
 * This avoids OS sleep-granularity drift at rates below ~5 k/s per thread.
 *
 * Config (env vars):
 *   KAFKA_BOOTSTRAP_SERVERS  default: kafka:29092
 *   KAFKA_TOPIC              default: crypto-trades
 *   LOAD_SYMBOLS             default: BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT
 *   LOAD_TRADES_PER_SECOND   default: 10000   (total across all threads)
 */
public class LoadGenerator {

    private static final Map<String, Double> SEED_PRICES = Map.of(
            "BTCUSDT", 85000.0,
            "ETHUSDT",  3200.0,
            "SOLUSDT",   140.0,
            "BNBUSDT",   580.0
    );

    public static void main(String[] args) throws Exception {
        String   bootstrapServers = env("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092");
        String   topic            = env("KAFKA_TOPIC",             "crypto-trades");
        String[] symbols          = env("LOAD_SYMBOLS",            "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT").split(",");
        int      totalTps         = Integer.parseInt(env("LOAD_TRADES_PER_SECOND", "10000"));
        int      numThreads       = symbols.length;
        long     tpsPerThread     = Math.max(1, totalTps / numThreads);

        System.out.printf("LoadGenerator started: %d trades/sec total  %d threads (%d/s each)  topic=%s%n",
                totalTps, numThreads, tpsPerThread, topic);

        // Single shared producer — KafkaProducer is thread-safe
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG,      bootstrapServers);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,   StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.LINGER_MS_CONFIG,              5);
        props.put(ProducerConfig.BATCH_SIZE_CONFIG,             65536);
        props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG,       "snappy");
        props.put(ProducerConfig.ACKS_CONFIG,                   "1");

        AtomicLong totalSent = new AtomicLong(0);
        AtomicLong tradeIdBase = new AtomicLong(System.currentTimeMillis() * 1000);

        try (KafkaProducer<String, String> producer = new KafkaProducer<>(props)) {

            // Stats reporter
            long startMs = System.currentTimeMillis();
            ScheduledExecutorService stats = Executors.newSingleThreadScheduledExecutor();
            stats.scheduleAtFixedRate(() -> {
                long elapsedSec = (System.currentTimeMillis() - startMs) / 1000;
                long sent = totalSent.get();
                System.out.printf("[stats] elapsed=%ds  sent=%d  rate=%.0f/s%n",
                        elapsedSec, sent, elapsedSec > 0 ? (double) sent / elapsedSec : 0);
            }, 5, 5, TimeUnit.SECONDS);

            // One worker thread per symbol
            ExecutorService pool = Executors.newFixedThreadPool(numThreads);
            for (String symbol : symbols) {
                final long perThreadTps = tpsPerThread;
                pool.submit(() -> runSymbol(symbol, topic, producer, tradeIdBase, totalSent, perThreadTps));
            }

            pool.awaitTermination(Long.MAX_VALUE, TimeUnit.DAYS);
        }
    }

    private static void runSymbol(String symbol, String topic,
                                   KafkaProducer<String, String> producer,
                                   AtomicLong tradeIdBase, AtomicLong totalSent,
                                   long tps) {
        ObjectMapper mapper = new ObjectMapper();
        Random       random = new Random();
        double price = SEED_PRICES.getOrDefault(symbol, 100.0);

        long startNs    = System.nanoTime();
        long sent       = 0;

        while (!Thread.currentThread().isInterrupted()) {
            try {
                // Advance price with Gaussian random walk (±0.03% per tick)
                price = Math.max(price + price * random.nextGaussian() * 0.0003, 0.01);

                double  qty          = Math.round((0.001 + random.nextDouble() * 0.5) * 10000.0) / 10000.0;
                boolean isBuyerMaker = random.nextBoolean();
                long    now          = System.currentTimeMillis();

                Map<String, Object> trade = new LinkedHashMap<>();
                trade.put("s",               symbol);
                trade.put("p",               Math.round(price * 100.0) / 100.0);
                trade.put("q",               qty);
                trade.put("T",               now);
                trade.put("m",               isBuyerMaker);
                trade.put("e",               "trade");
                trade.put("E",               now);
                trade.put("t",               tradeIdBase.getAndIncrement());
                trade.put("source",          "LOADGEN");
                trade.put("ingestionTimeMs", now);
                trade.put("latencyMs",       0);

                producer.send(new ProducerRecord<>(topic, symbol, mapper.writeValueAsString(trade)));
                totalSent.incrementAndGet();
                sent++;

                // Lag-compensating rate limiter:
                // Sleep only if we are ahead of the target schedule.
                long elapsedNs    = System.nanoTime() - startNs;
                long targetSent   = elapsedNs * tps / 1_000_000_000L;
                long aheadMs      = (sent - targetSent) * 1000 / tps;
                if (aheadMs > 1) {
                    Thread.sleep(aheadMs);
                }

            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            } catch (Exception e) {
                System.err.println("[" + symbol + "] error: " + e.getMessage());
            }
        }
    }

    private static String env(String key, String defaultValue) {
        return System.getenv().getOrDefault(key, defaultValue);
    }
}
