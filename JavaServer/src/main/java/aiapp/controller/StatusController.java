package aiapp.controller;

import aiapp.service.AiService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class StatusController {
    private final AiService aiService;

    public StatusController(AiService aiService) {
        this.aiService = aiService;
    }

    @GetMapping("/status")
    public Map<String, String> status() {
        return Map.of("ai_status", aiService.checkStatus());
    }
}
