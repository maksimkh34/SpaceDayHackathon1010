package aiapp.controller;

import aiapp.dto.UploadResponse;
import aiapp.service.AiService;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api")
public class UploadController {
    private final AiService aiService;

    public UploadController(AiService aiService) {
        this.aiService = aiService;
    }

    @PostMapping("/upload")
    public UploadResponse upload(@RequestParam("file") MultipartFile file) throws Exception {
        return aiService.analyzeImage(file.getBytes());
    }
}
