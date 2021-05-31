/*
 * Decompiled with CFR 0_125.
 *
 * Could not load the following classes:
 *  com.dpbg.school.auth.config.CustomTokenEnhancer
 *  com.dpbg.school.auth.model.CustomUserDetails
 *  com.dpbg.school.auth.service.impl.CustomUserDetailsService
 *  kotlin.Metadata
 *  kotlin.jvm.internal.Intrinsics
 *  org.jetbrains.annotations.NotNull
 *  org.springframework.security.oauth2.common.DefaultOAuth2AccessToken
 *  org.springframework.security.oauth2.common.OAuth2AccessToken
 *  org.springframework.security.oauth2.provider.OAuth2Authentication
 *  org.springframework.security.oauth2.provider.token.TokenEnhancer
 */
package com.dpbg.school.auth.config;

import com.dpbg.school.auth.model.CustomUserDetails;
import com.dpbg.school.auth.service.impl.CustomUserDetailsService;
import java.util.HashMap;
import java.util.Map;
import kotlin.Metadata;
import kotlin.jvm.internal.Intrinsics;
import org.jetbrains.annotations.NotNull;
import org.springframework.security.oauth2.common.DefaultOAuth2AccessToken;
import org.springframework.security.oauth2.common.OAuth2AccessToken;
import org.springframework.security.oauth2.provider.OAuth2Authentication;
import org.springframework.security.oauth2.provider.token.TokenEnhancer;

@Metadata(mv={1, 1, 9}, bv={1, 0, 2}, k=1, d1={"\u0000 \n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\u0018\u00002\u00020\u0001B\r\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\u0002\u0010\u0004J\u0018\u0010\u0005\u001a\u00020\u00062\u0006\u0010\u0007\u001a\u00020\u00062\u0006\u0010\b\u001a\u00020\tH\u0016R\u000e\u0010\u0002\u001a\u00020\u0003X\u0082\u0004\u00a2\u0006\u0002\n\u0000\u00a8\u0006\n"}, d2={"Lcom/dpbg/school/auth/config/CustomTokenEnhancer;", "Lorg/springframework/security/oauth2/provider/token/TokenEnhancer;", "userDetailsService", "Lcom/dpbg/school/auth/service/impl/CustomUserDetailsService;", "(Lcom/dpbg/school/auth/service/impl/CustomUserDetailsService;)V", "enhance", "Lorg/springframework/security/oauth2/common/OAuth2AccessToken;", "accessToken", "authentication", "Lorg/springframework/security/oauth2/provider/OAuth2Authentication;", "auth-service"})
public final class CustomTokenEnhancer
implements TokenEnhancer {
    private final CustomUserDetailsService userDetailsService;

    @NotNull
    public OAuth2AccessToken enhance(@NotNull OAuth2AccessToken accessToken, @NotNull OAuth2Authentication authentication) {
        Intrinsics.checkParameterIsNotNull((Object)accessToken, (String)"accessToken");
        Intrinsics.checkParameterIsNotNull((Object)authentication, (String)"authentication");
        String string = authentication.getName();
        Intrinsics.checkExpressionValueIsNotNull((Object)string, (String)"authentication.name");
        CustomUserDetails userDetails = this.userDetailsService.loadUserByUsername(string);
        HashMap additionalInfo = new HashMap();
        Map map = additionalInfo;
        String string2 = "firstName";
        String string3 = userDetails.getFirstName();
        map.put(string2, string3);
        map = additionalInfo;
        string2 = "lastName";
        string3 = userDetails.getLastName();
        map.put(string2, string3);
        map = additionalInfo;
        string2 = "id";
        string3 = userDetails.getId();
        map.put(string2, string3);
        map = additionalInfo;
        string2 = "role_name";
        string3 = userDetails.getRoleName();
        map.put(string2, string3);
        ((DefaultOAuth2AccessToken)accessToken).setAdditionalInformation((Map)additionalInfo);
        return accessToken;
    }

    public CustomTokenEnhancer(@NotNull CustomUserDetailsService userDetailsService) {
        Intrinsics.checkParameterIsNotNull((Object)userDetailsService, (String)"userDetailsService");
        this.userDetailsService = userDetailsService;
    }
}