plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "de.hotelaquarius.voiceclaude"
    compileSdk = 34

    defaultConfig {
        applicationId = "de.hotelaquarius.voiceclaude"
        // Galaxy S23 läuft mit Android 13+, minSdk 26 deckt aber auch ältere Testgeräte ab.
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = true
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    implementation("androidx.preference:preference-ktx:1.2.1")
    // HTTP-Client für die Anthropic Messages API
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    // Coroutines für asynchrone Netzwerk-Calls
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
}
