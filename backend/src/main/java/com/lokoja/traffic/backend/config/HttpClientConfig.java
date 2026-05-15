package com.lokoja.traffic.backend.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class HttpClientConfig {

    @Bean
    RestClient mlRestClient(RestClient.Builder builder,
                            MlServiceProperties properties) {
        return builder
                .baseUrl(properties.getBaseUrl())
                .build();
    }
}
