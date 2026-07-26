package com.finlens.aggregation.security;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.junit.jupiter.api.Test;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

class JwtServiceTest {

    @Test
    void jwtServiceCanCreateAndParseToken() {
        JwtService jwtService = new JwtService("this-is-a-very-long-secret-key-for-jwt-signing-1234567890", 3600000L);
        String token = jwtService.generateToken(42L);

        assertNotNull(token);
        assertEquals(42L, jwtService.extractUserId(token));
    }

    @Test
    void passwordEncoderHashesAndVerifiesPasswords() {
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
        String encoded = encoder.encode("secret123");

        assertNotNull(encoded);
        assertEquals(true, encoder.matches("secret123", encoded));
    }
}
