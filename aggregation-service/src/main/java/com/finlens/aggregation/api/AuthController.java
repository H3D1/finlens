package com.finlens.aggregation.api;

import com.finlens.aggregation.model.User;
import com.finlens.aggregation.repository.UserRepository;
import com.finlens.aggregation.security.JwtService;
import java.util.Map;
import java.util.Optional;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthController(UserRepository userRepository, PasswordEncoder passwordEncoder, JwtService jwtService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody RegisterRequest request) {
        Optional<User> existingUser = userRepository.findByEmail(request.email());
        if (existingUser.isPresent()) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("message", "User already exists"));
        }

        User user = userRepository.save(new User(request.email(), passwordEncoder.encode(request.password())));
        String token = jwtService.generateToken(user.getId());

        return ResponseEntity.status(HttpStatus.CREATED)
                .body(Map.of("token", token, "userId", user.getId(), "email", user.getEmail()));
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody LoginRequest request) {
        User user = userRepository.findByEmail(request.email())
                .orElseThrow(() -> new IllegalArgumentException("Invalid credentials"));

        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new IllegalArgumentException("Invalid credentials");
        }

        String token = jwtService.generateToken(user.getId());
        return ResponseEntity.ok(Map.of("token", token, "userId", user.getId(), "email", user.getEmail()));
    }

    public record RegisterRequest(String email, String password) {
    }

    public record LoginRequest(String email, String password) {
    }
}
