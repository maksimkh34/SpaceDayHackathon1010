package aiapp.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                // отключаем CSRF для /auth/**
                .csrf(csrf -> csrf.ignoringRequestMatchers("/auth/**"))
                // разрешаем все /auth/** и требуем аутентификацию для остальных
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/auth/**").permitAll()
                        .anyRequest().authenticated()
                );

        // Больше не вызываем httpBasic() и formLogin()
        // Всё что нужно для REST API — это разрешить /auth/** и отключить CSRF

        return http.build();
    }
}
