package aiapp.service;

import aiapp.dto.AuthRequest;
import aiapp.dto.AuthResponse;
import aiapp.entity.User;
import aiapp.repository.UserRepository;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class AuthService {
    private final UserRepository userRepository;

    public AuthService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public AuthResponse register(AuthRequest request) {
        User user = User.builder()
                .username(request.getUsername())
                .password(request.getPassword()) // для прототипа храним plain
                .build();
        userRepository.save(user);
        return new AuthResponse("dummy-token"); // позже JWT
    }

    public AuthResponse login(AuthRequest request) {
        Optional<User> userOpt = userRepository.findByUsername(request.getUsername());
        if (userOpt.isPresent() && userOpt.get().getPassword().equals(request.getPassword())) {
            return new AuthResponse("dummy-token");
        }
        throw new RuntimeException("Invalid credentials");
    }
}
