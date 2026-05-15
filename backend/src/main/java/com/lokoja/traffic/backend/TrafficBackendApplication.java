package com.lokoja.traffic.backend;

import com.lokoja.traffic.backend.config.MlServiceProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(MlServiceProperties.class)
public class TrafficBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(TrafficBackendApplication.class, args);
    }
}
