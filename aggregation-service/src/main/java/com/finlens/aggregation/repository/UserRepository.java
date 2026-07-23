package com.finlens.aggregation.repository;

import com.finlens.aggregation.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {
}