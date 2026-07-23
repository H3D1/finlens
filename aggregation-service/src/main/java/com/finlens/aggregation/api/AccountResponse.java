package com.finlens.aggregation.api;

import com.finlens.aggregation.model.Account;
import com.finlens.aggregation.model.Transaction;
import java.util.List;

public record AccountResponse(Account account, List<Transaction> transactions) {
}