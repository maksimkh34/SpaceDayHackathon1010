package aiapp.service;

import aiapp.dto.AuthRequest;
import aiapp.dto.AuthResponse;
import aiapp.entity.User;
import aiapp.repository.UserRepository;
import aiapp.util.PasswordUtil;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class AuthService {

    private final UserRepository userRepository;

    public AuthService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    /**
     * Регистрация нового пользователя.
     * Пароль хэшируется с помощью BCrypt.
     */
    public AuthResponse register(AuthRequest request) {
        // Проверяем, что пользователь с таким email не существует
        if (userRepository.findByEmail(request.getUsername()).isPresent()) {
            throw new RuntimeException("Email уже зарегистрирован");
        }

        // Хэшируем пароль
        String hashed = PasswordUtil.hashPassword(request.getPassword());

        // Создаём нового пользователя
        User user = User.builder()
                .email(request.getUsername())
                .passHash(hashed)
                .isConfirmed(true)
                .build();

        userRepository.save(user);

        // Возвращаем тестовый токен (можно заменить на JWT позже)
        return new AuthResponse("dummy-token-" + user.getId());
    }

    /**
     * Авторизация пользователя.
     * Проверяется соответствие пароля хэшу.
     */
    public AuthResponse login(AuthRequest request) {
        Optional<User> userOpt = userRepository.findByEmail(request.getUsername());

        if (userOpt.isEmpty()) {
            throw new RuntimeException("Пользователь не найден");
        }

        User user = userOpt.get();

        if (!PasswordUtil.verifyPassword(request.getPassword(), user.getPassHash())) {
            throw new RuntimeException("Неверный пароль");
        }

        // Возвращаем тестовый токен (можно заменить на JWT позже)
        return new AuthResponse("dummy-token-" + user.getId());
    }
}
