package aiapp.service;

import aiapp.dto.UploadResponse;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class AiService {

    public UploadResponse analyzeImage(byte[] image) {
        // Здесь позже будет WebClient к AI
        return new UploadResponse(
                "success",
                "dummy-result",
                LocalDateTime.now().toString()
        );
    }

    public String checkStatus() {
        return "running"; // заглушка
    }
}
