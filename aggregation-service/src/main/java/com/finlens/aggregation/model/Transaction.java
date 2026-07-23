package com.finlens.aggregation.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
public class Transaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long accountId;

    private BigDecimal amount;

    private String description;

    private Instant timestamp;

    private String category;

    protected Transaction() {
    }

    public Transaction(Long accountId, BigDecimal amount, String description, Instant timestamp, String category) {
        this.accountId = accountId;
        this.amount = amount;
        this.description = description;
        this.timestamp = timestamp;
        this.category = category;
    }

    public Long getId() {
        return id;
    }

    public Long getAccountId() {
        return accountId;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public String getDescription() {
        return description;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public String getCategory() {
        return category;
    }
}