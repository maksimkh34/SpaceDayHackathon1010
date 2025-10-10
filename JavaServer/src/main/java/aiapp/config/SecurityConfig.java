package aiapp.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

import static org.springframework.security.config.Customizer.withDefaults;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // Disable CSRF - modern lambda style
                .csrf(AbstractHttpConfigurer::disable)
                // Enable CORS with your configuration
                .cors(cors -> cors.configurationSource(yourCorsConfigurationSource())) // ✅ Важно: включите CORS
                // Configure authorization
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/auth/**").permitAll() // Allow access to auth endpoints
                        .anyRequest().authenticated()
                )
                // Optional: Enable basic auth if needed
                .httpBasic(withDefaults());

        return http.build();
    }

    // CORS configuration source
    @Bean
    public CorsConfigurationSource yourCorsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        // Для разработки можно разрешить все источники, но для продакшена укажите конкретный
        configuration.setAllowedOrigins(List.of("*")); // ✅ Или "http://localhost:3000" для вашего фронтенда
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("*"));
        // Если вы не передаете куки или авторизационные заголовки, allowCredentials не нужен
        // configuration.setAllowCredentials(true); // Если используется, то allowedOrigins не может быть "*"

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}