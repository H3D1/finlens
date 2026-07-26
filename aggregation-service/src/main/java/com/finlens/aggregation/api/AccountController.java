package com.finlens.aggregation.api;

import com.finlens.aggregation.repository.AccountRepository;
import com.finlens.aggregation.repository.TransactionRepository;
import java.util.List;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/accounts")
public class AccountController {

    private final AccountRepository accountRepository;
    private final TransactionRepository transactionRepository;

    public AccountController(AccountRepository accountRepository, TransactionRepository transactionRepository) {
        this.accountRepository = accountRepository;
        this.transactionRepository = transactionRepository;
    }

    @GetMapping
    public List<AccountResponse> getAccounts(Authentication authentication) {
        Long userId = Long.valueOf(authentication.getName());

        return accountRepository.findByUserId(userId).stream()
                .map(account -> new AccountResponse(account, transactionRepository.findByAccountIdOrderByTimestampDesc(account.getId())))
                .toList();
    }
}