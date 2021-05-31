/*
 * Decompiled with CFR 0_125.
 *
 * Could not load the following classes:
 *  com.dpbg.school.auth.config.CustomTokenEnhancer
 *  com.dpbg.school.auth.config.OAuth2ServerConfig
 *  com.dpbg.school.auth.service.impl.CustomUserDetailsService
 *  kotlin.Metadata
 *  kotlin.collections.CollectionsKt
 *  kotlin.jvm.internal.Intrinsics
 *  org.jetbrains.annotations.NotNull
 *  org.jetbrains.annotations.Nullable
 *  org.springframework.beans.factory.annotation.Value
 *  org.springframework.context.annotation.Bean
 *  org.springframework.context.annotation.Configuration
 *  org.springframework.context.annotation.Primary
 *  org.springframework.http.HttpMethod
 *  org.springframework.security.authentication.AuthenticationManager
 *  org.springframework.security.core.userdetails.UserDetailsService
 *  org.springframework.security.crypto.password.PasswordEncoder
 *  org.springframework.security.oauth2.config.annotation.builders.ClientDetailsServiceBuilder
 *  org.springframework.security.oauth2.config.annotation.builders.ClientDetailsServiceBuilder$ClientBuilder
 *  org.springframework.security.oauth2.config.annotation.builders.InMemoryClientDetailsServiceBuilder
 *  org.springframework.security.oauth2.config.annotation.configurers.ClientDetailsServiceConfigurer
 *  org.springframework.security.oauth2.config.annotation.web.configuration.AuthorizationServerConfigurerAdapter
 *  org.springframework.security.oauth2.config.annotation.web.configuration.EnableAuthorizationServer
 *  org.springframework.security.oauth2.config.annotation.web.configurers.AuthorizationServerEndpointsConfigurer
 *  org.springframework.security.oauth2.config.annotation.web.configurers.AuthorizationServerSecurityConfigurer
 *  org.springframework.security.oauth2.provider.token.AccessTokenConverter
 *  org.springframework.security.oauth2.provider.token.DefaultTokenServices
 *  org.springframework.security.oauth2.provider.token.TokenEnhancer
 *  org.springframework.security.oauth2.provider.token.TokenEnhancerChain
 *  org.springframework.security.oauth2.provider.token.TokenStore
 *  org.springframework.security.oauth2.provider.token.store.JwtAccessTokenConverter
 *  org.springframework.security.oauth2.provider.token.store.JwtTokenStore
 */
package com.dpbg.school.auth.config;

import com.dpbg.school.auth.config.CustomTokenEnhancer;
import com.dpbg.school.auth.service.impl.CustomUserDetailsService;
import java.util.List;
import kotlin.Metadata;
import kotlin.collections.CollectionsKt;
import kotlin.jvm.internal.Intrinsics;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.oauth2.config.annotation.builders.ClientDetailsServiceBuilder;
import org.springframework.security.oauth2.config.annotation.builders.InMemoryClientDetailsServiceBuilder;
import org.springframework.security.oauth2.config.annotation.configurers.ClientDetailsServiceConfigurer;
import org.springframework.security.oauth2.config.annotation.web.configuration.AuthorizationServerConfigurerAdapter;
import org.springframework.security.oauth2.config.annotation.web.configuration.EnableAuthorizationServer;
import org.springframework.security.oauth2.config.annotation.web.configurers.AuthorizationServerEndpointsConfigurer;
import org.springframework.security.oauth2.config.annotation.web.configurers.AuthorizationServerSecurityConfigurer;
import org.springframework.security.oauth2.provider.token.AccessTokenConverter;
import org.springframework.security.oauth2.provider.token.DefaultTokenServices;
import org.springframework.security.oauth2.provider.token.TokenEnhancer;
import org.springframework.security.oauth2.provider.token.TokenEnhancerChain;
import org.springframework.security.oauth2.provider.token.TokenStore;
import org.springframework.security.oauth2.provider.token.store.JwtAccessTokenConverter;
import org.springframework.security.oauth2.provider.token.store.JwtTokenStore;

@Configuration
@EnableAuthorizationServer
@Metadata(mv={1, 1, 9}, bv={1, 0, 2}, k=1, d1={"\u0000V\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0006\n\u0002\u0010\u000e\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\b\u0017\u0018\u00002\u00020\u0001B\u001d\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u0012\u0006\u0010\u0004\u001a\u00020\u0005\u0012\u0006\u0010\u0006\u001a\u00020\u0007\u00a2\u0006\u0002\u0010\bJ\b\u0010\u0011\u001a\u00020\u0012H\u0017J\u0010\u0010\u0013\u001a\u00020\u00142\u0006\u0010\u0015\u001a\u00020\u0016H\u0017J\u0012\u0010\u0013\u001a\u00020\u00142\b\u0010\u0017\u001a\u0004\u0018\u00010\u0018H\u0017J\u0012\u0010\u0013\u001a\u00020\u00142\b\u0010\u0019\u001a\u0004\u0018\u00010\u001aH\u0017J\u0010\u0010\u001b\u001a\u00020\u001c2\u0006\u0010\u0002\u001a\u00020\u0003H\u0017J\b\u0010\u001d\u001a\u00020\u001eH\u0017J\b\u0010\u001f\u001a\u00020 H\u0017R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096\u0004\u00a2\u0006\b\n\u0000\u001a\u0004\b\t\u0010\nR\u0014\u0010\u0006\u001a\u00020\u0007X\u0096\u0004\u00a2\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\fR\u0012\u0010\r\u001a\u0004\u0018\u00010\u000e8\u0012X\u0093\u0004\u00a2\u0006\u0002\n\u0000R\u0014\u0010\u0002\u001a\u00020\u0003X\u0096\u0004\u00a2\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010\u00a8\u0006!"}, d2={"Lcom/dpbg/school/auth/config/OAuth2ServerConfig;", "Lorg/springframework/security/oauth2/config/annotation/web/configuration/AuthorizationServerConfigurerAdapter;", "userDetailsService", "Lcom/dpbg/school/auth/service/impl/CustomUserDetailsService;", "authenticationManager", "Lorg/springframework/security/authentication/AuthenticationManager;", "passwordEncoder", "Lorg/springframework/security/crypto/password/PasswordEncoder;", "(Lcom/dpbg/school/auth/service/impl/CustomUserDetailsService;Lorg/springframework/security/authentication/AuthenticationManager;Lorg/springframework/security/crypto/password/PasswordEncoder;)V", "getAuthenticationManager", "()Lorg/springframework/security/authentication/AuthenticationManager;", "getPasswordEncoder", "()Lorg/springframework/security/crypto/password/PasswordEncoder;", "signingKey", "", "getUserDetailsService", "()Lcom/dpbg/school/auth/service/impl/CustomUserDetailsService;", "accessTokenConverter", "Lorg/springframework/security/oauth2/provider/token/store/JwtAccessTokenConverter;", "configure", "", "clients", "Lorg/springframework/security/oauth2/config/annotation/configurers/ClientDetailsServiceConfigurer;", "endpoints", "Lorg/springframework/security/oauth2/config/annotation/web/configurers/AuthorizationServerEndpointsConfigurer;", "oauthServer", "Lorg/springframework/security/oauth2/config/annotation/web/configurers/AuthorizationServerSecurityConfigurer;", "tokenEnhancer", "Lorg/springframework/security/oauth2/provider/token/TokenEnhancer;", "tokenServices", "Lorg/springframework/security/oauth2/provider/token/DefaultTokenServices;", "tokenStore", "Lorg/springframework/security/oauth2/provider/token/TokenStore;", "auth-service"})
public class OAuth2ServerConfig
extends AuthorizationServerConfigurerAdapter {
    @Value(value="${signing_key}")
    private final String signingKey;
    @NotNull
    private final CustomUserDetailsService userDetailsService;
    @NotNull
    private final AuthenticationManager authenticationManager;
    @NotNull
    private final PasswordEncoder passwordEncoder;

    public void configure(@Nullable AuthorizationServerEndpointsConfigurer endpoints) throws Exception {
        TokenEnhancerChain tokenEnhancerChain = new TokenEnhancerChain();
        tokenEnhancerChain.setTokenEnhancers(CollectionsKt.listOf((Object[])new TokenEnhancer[]{this.tokenEnhancer(this.getUserDetailsService()), (TokenEnhancer)this.accessTokenConverter()}));
        AuthorizationServerEndpointsConfigurer authorizationServerEndpointsConfigurer = endpoints;
        if (authorizationServerEndpointsConfigurer == null) {
            Intrinsics.throwNpe();
        }
        authorizationServerEndpointsConfigurer.tokenStore(this.tokenStore()).tokenEnhancer((TokenEnhancer)tokenEnhancerChain).accessTokenConverter((AccessTokenConverter)this.accessTokenConverter()).authenticationManager(this.getAuthenticationManager()).userDetailsService((UserDetailsService)this.getUserDetailsService()).allowedTokenEndpointRequestMethods(new HttpMethod[]{HttpMethod.GET, HttpMethod.POST});
    }

    @Bean
    @NotNull
    public TokenStore tokenStore() {
        return (TokenStore)new JwtTokenStore(this.accessTokenConverter());
    }

    @Bean
    @NotNull
    public JwtAccessTokenConverter accessTokenConverter() {
        JwtAccessTokenConverter converter = new JwtAccessTokenConverter();
        String string = this.signingKey;
        if (string == null) {
            Intrinsics.throwNpe();
        }
        converter.setSigningKey(string);
        return converter;
    }

    @Bean
    @Primary
    @NotNull
    public DefaultTokenServices tokenServices() {
        DefaultTokenServices defaultTokenServices = new DefaultTokenServices();
        defaultTokenServices.setTokenStore(this.tokenStore());
        defaultTokenServices.setSupportRefreshToken(true);
        return defaultTokenServices;
    }

    public void configure(@NotNull ClientDetailsServiceConfigurer clients) throws Exception {
        Intrinsics.checkParameterIsNotNull((Object)clients, (String)"clients");
        clients.inMemory().withClient("clientapp").secret(this.getPasswordEncoder().encode((CharSequence)"123456")).authorizedGrantTypes(new String[]{"implicit", "password", "authorization_code", "refresh_token"}).scopes(new String[]{"read", "write"}).accessTokenValiditySeconds(86400).refreshTokenValiditySeconds(172800);
    }

    @Bean
    @NotNull
    public TokenEnhancer tokenEnhancer(@NotNull CustomUserDetailsService userDetailsService) {
        Intrinsics.checkParameterIsNotNull((Object)userDetailsService, (String)"userDetailsService");
        return (TokenEnhancer)new CustomTokenEnhancer(userDetailsService);
    }

    public void configure(@Nullable AuthorizationServerSecurityConfigurer oauthServer) throws Exception {
        AuthorizationServerSecurityConfigurer authorizationServerSecurityConfigurer = oauthServer;
        if (authorizationServerSecurityConfigurer == null) {
            Intrinsics.throwNpe();
        }
        authorizationServerSecurityConfigurer.allowFormAuthenticationForClients().tokenKeyAccess("permitAll()");
    }

    @NotNull
    public CustomUserDetailsService getUserDetailsService() {
        return this.userDetailsService;
    }

    @NotNull
    public AuthenticationManager getAuthenticationManager() {
        return this.authenticationManager;
    }

    @NotNull
    public PasswordEncoder getPasswordEncoder() {
        return this.passwordEncoder;
    }

    public OAuth2ServerConfig(@NotNull CustomUserDetailsService userDetailsService, @NotNull AuthenticationManager authenticationManager, @NotNull PasswordEncoder passwordEncoder) {
        Intrinsics.checkParameterIsNotNull((Object)userDetailsService, (String)"userDetailsService");
        Intrinsics.checkParameterIsNotNull((Object)authenticationManager, (String)"authenticationManager");
        Intrinsics.checkParameterIsNotNull((Object)passwordEncoder, (String)"passwordEncoder");
        this.userDetailsService = userDetailsService;
        this.authenticationManager = authenticationManager;
        this.passwordEncoder = passwordEncoder;
    }
}