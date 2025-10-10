package aiapp.controller;

import aiapp.dto.AuthRequest;
import aiapp.dto.AuthResponse;
import aiapp.service.AuthService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/auth/register")
    public AuthResponse register(@RequestBody AuthRequest request) {
        System.out.println("Received request: " + request.getUsername());
        return authService.register(request);
    }


    @PostMapping("/login")
    public AuthResponse login(@RequestBody AuthRequest request) {
        return authService.login(request);
    }
}
