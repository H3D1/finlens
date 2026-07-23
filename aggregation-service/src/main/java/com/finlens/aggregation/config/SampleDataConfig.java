package com.finlens.aggregation.config;

import com.finlens.aggregation.model.Account;
import com.finlens.aggregation.model.Transaction;
import com.finlens.aggregation.model.User;
import com.finlens.aggregation.repository.AccountRepository;
import com.finlens.aggregation.repository.TransactionRepository;
import com.finlens.aggregation.repository.UserRepository;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SampleDataConfig {

    @Bean
    CommandLineRunner seedSampleData(UserRepository userRepository, AccountRepository accountRepository,
                                     TransactionRepository transactionRepository) {
        return args -> {
            if (accountRepository.count() > 0) {
                return;
            }

            User user = userRepository.save(new User("alex@example.com", "placeholder-password-hash"));
            Account checking = accountRepository.save(new Account(user.getId(), Account.Type.CHECKING,
                    new BigDecimal("2450.75"), "USD"));
            Account savings = accountRepository.save(new Account(user.getId(), Account.Type.SAVINGS,
                    new BigDecimal("12800.00"), "USD"));
            Account creditCard = accountRepository.save(new Account(user.getId(), Account.Type.CREDIT_CARD,
                    new BigDecimal("-842.19"), "USD"));

            Instant now = Instant.now();
            transactionRepository.saveAll(List.of(
                    new Transaction(checking.getId(), new BigDecimal("3200.00"), "Paycheck", now.minus(2, ChronoUnit.DAYS), "income"),
                    new Transaction(checking.getId(), new BigDecimal("-84.50"), "Grocery market", now.minus(1, ChronoUnit.DAYS), "groceries"),
                    new Transaction(checking.getId(), new BigDecimal("-52.00"), "Electric utility", now.minus(5, ChronoUnit.DAYS), "utilities"),
                    new Transaction(savings.getId(), new BigDecimal("500.00"), "Transfer from checking", now.minus(3, ChronoUnit.DAYS), "transfer"),
                    new Transaction(savings.getId(), new BigDecimal("12.40"), "Interest payment", now.minus(10, ChronoUnit.DAYS), "interest"),
                    new Transaction(creditCard.getId(), new BigDecimal("-74.99"), "Streaming subscription", now.minus(1, ChronoUnit.DAYS), "entertainment"),
                    new Transaction(creditCard.getId(), new BigDecimal("-124.25"), "Home improvement", now.minus(4, ChronoUnit.DAYS), "shopping"),
                    new Transaction(creditCard.getId(), new BigDecimal("-36.80"), "Restaurant", now.minus(6, ChronoUnit.DAYS), "dining")
            ));
        };
    }
}