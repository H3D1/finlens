package com.finlens.aggregation.repository;

import com.finlens.aggregation.model.Account;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountRepository extends JpaRepository<Account, Long> {
}