# kotlinx.serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.SerializationKt
-keep,includedescriptorclasses class dev.limitwatch.**$$serializer { *; }
-keepclassmembers class dev.limitwatch.** {
    *** Companion;
}
-keepclasseswithmembers class dev.limitwatch.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# Ktor OkHttp engine
-keep class io.ktor.** { *; }
-keep class okhttp3.** { *; }
-keep class okio.** { *; }
-dontwarn org.slf4j.**
-dontwarn org.conscrypt.**
