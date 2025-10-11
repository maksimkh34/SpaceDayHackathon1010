package aiapp.util;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class PasswordUtil {

    private static final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    /**
     * Хэширует пароль с использованием BCrypt.
     * @param rawPassword исходный пароль в обычном виде
     * @return BCrypt-хэш (с солью)
     */
    public static String hashPassword(String rawPassword) {
        return encoder.encode(rawPassword);
    }

    /**
     * Проверяет, совпадает ли исходный пароль с хэшом.
     * @param rawPassword введённый пользователем пароль
     * @param hashedPassword пароль, сохранённый в БД
     * @return true если совпадает
     */
    public static boolean verifyPassword(String rawPassword, String hashedPassword) {
        return encoder.matches(rawPassword, hashedPassword);
    }
}
