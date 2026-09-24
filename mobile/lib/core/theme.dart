// ═══════════════════════════════════════════════════════════
// H1-AI Mobile — Professional Theme
// ═══════════════════════════════════════════════════════════
import 'package:flutter/material.dart';

// ═══ Colors ═══
class AppColors {
  // Primary
  static const primary50 = Color(0xFFF0F9FF);
  static const primary100 = Color(0xFFE0F2FE);
  static const primary200 = Color(0xFFBAE6FD);
  static const primary300 = Color(0xFF7DD3FC);
  static const primary400 = Color(0xFF38BDF8);
  static const primary500 = Color(0xFF0EA5E9);
  static const primary600 = Color(0xFF0284C7);
  static const primary700 = Color(0xFF0369A1);
  static const primary800 = Color(0xFF075985);
  static const primary900 = Color(0xFF0C4A6E);

  // Accent
  static const accent500 = Color(0xFF8B5CF6);
  static const accent600 = Color(0xFF7C3AED);

  // Success
  static const success50 = Color(0xFFF0FDF4);
  static const success500 = Color(0xFF10B981);
  static const success600 = Color(0xFF059669);

  // Warning
  static const warning50 = Color(0xFFFFFBEB);
  static const warning500 = Color(0xFFF59E0B);
  static const warning600 = Color(0xFFD97706);

  // Error
  static const error50 = Color(0xFFFEF2F2);
  static const error500 = Color(0xFFEF4444);
  static const error600 = Color(0xFFDC2626);

  // Neutral
  static const gray50 = Color(0xFFF8FAFC);
  static const gray100 = Color(0xFFF1F5F9);
  static const gray200 = Color(0xFFE2E8F0);
  static const gray300 = Color(0xFFCBD5E1);
  static const gray400 = Color(0xFF94A3B8);
  static const gray500 = Color(0xFF64748B);
  static const gray600 = Color(0xFF475569);
  static const gray700 = Color(0xFF334155);
  static const gray800 = Color(0xFF1E293B);
  static const gray900 = Color(0xFF0F172A);
  static const gray950 = Color(0xFF020617);
}

// ═══ Shadows ═══
class AppShadows {
  static final sm = [
    BoxShadow(
      color: Colors.black.withOpacity(0.05),
      blurRadius: 2,
      offset: const Offset(0, 1),
    ),
  ];

  static final md = [
    BoxShadow(
      color: Colors.black.withOpacity(0.08),
      blurRadius: 8,
      offset: const Offset(0, 4),
    ),
  ];

  static final lg = [
    BoxShadow(
      color: Colors.black.withOpacity(0.1),
      blurRadius: 16,
      offset: const Offset(0, 8),
    ),
  ];

  static final xl = [
    BoxShadow(
      color: Colors.black.withOpacity(0.12),
      blurRadius: 24,
      offset: const Offset(0, 12),
    ),
  ];
}

// ═══ Light Theme ═══
ThemeData get lightTheme => ThemeData(
  useMaterial3: true,
  brightness: Brightness.light,
  colorScheme: ColorScheme.fromSeed(
    seedColor: AppColors.primary500,
    brightness: Brightness.light,
    primary: AppColors.primary500,
    secondary: AppColors.accent500,
    error: AppColors.error500,
  ),
  scaffoldBackgroundColor: AppColors.gray50,
  fontFamily: 'Cairo',
  fontFamilyFallback: const ['Tajawal', 'sans-serif'],
  
  // AppBar
  appBarTheme: AppBarTheme(
    elevation: 0,
    centerTitle: true,
    backgroundColor: Colors.white,
    foregroundColor: AppColors.gray900,
    surfaceTintColor: Colors.transparent,
    titleTextStyle: const TextStyle(
      fontFamily: 'Cairo',
      fontSize: 20,
      fontWeight: FontWeight.w700,
      color: AppColors.gray900,
    ),
    shadowColor: Colors.black.withOpacity(0.05),
  ),
  
  // Cards
  cardTheme: CardTheme(
    elevation: 0,
    color: Colors.white,
    surfaceTintColor: Colors.transparent,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(20),
      side: const BorderSide(color: AppColors.gray200, width: 1),
    ),
    margin: EdgeInsets.zero,
  ),
  
  // Buttons
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: AppColors.primary500,
      foregroundColor: Colors.white,
      elevation: 0,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
      ),
      textStyle: const TextStyle(
        fontFamily: 'Cairo',
        fontSize: 16,
        fontWeight: FontWeight.w600,
      ),
    ),
  ),
  
  // Input
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: AppColors.gray100,
    contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide.none,
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide.none,
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: const BorderSide(color: AppColors.primary500, width: 2),
    ),
    hintStyle: const TextStyle(
      fontFamily: 'Cairo',
      color: AppColors.gray400,
      fontSize: 15,
    ),
  ),
  
  // Chip
  chipTheme: ChipThemeData(
    backgroundColor: AppColors.gray100,
    selectedColor: AppColors.primary100,
    side: BorderSide.none,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(10),
    ),
    labelStyle: const TextStyle(
      fontFamily: 'Cairo',
      fontWeight: FontWeight.w600,
    ),
  ),
);

// ═══ Dark Theme ═══
ThemeData get darkTheme => ThemeData(
  useMaterial3: true,
  brightness: Brightness.dark,
  colorScheme: ColorScheme.fromSeed(
    seedColor: AppColors.primary500,
    brightness: Brightness.dark,
    primary: AppColors.primary400,
    secondary: AppColors.accent500,
    error: AppColors.error500,
  ),
  scaffoldBackgroundColor: AppColors.gray950,
  fontFamily: 'Cairo',
  fontFamilyFallback: const ['Tajawal', 'sans-serif'],
  
  appBarTheme: AppBarTheme(
    elevation: 0,
    centerTitle: true,
    backgroundColor: AppColors.gray900,
    foregroundColor: AppColors.gray50,
    surfaceTintColor: Colors.transparent,
    titleTextStyle: const TextStyle(
      fontFamily: 'Cairo',
      fontSize: 20,
      fontWeight: FontWeight.w700,
      color: AppColors.gray50,
    ),
  ),
  
  cardTheme: CardTheme(
    elevation: 0,
    color: AppColors.gray800,
    surfaceTintColor: Colors.transparent,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(20),
      side: const BorderSide(color: AppColors.gray700, width: 1),
    ),
    margin: EdgeInsets.zero,
  ),
  
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: AppColors.primary500,
      foregroundColor: Colors.white,
      elevation: 0,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
      ),
      textStyle: const TextStyle(
        fontFamily: 'Cairo',
        fontSize: 16,
        fontWeight: FontWeight.w600,
      ),
    ),
  ),
  
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: AppColors.gray800,
    contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide.none,
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide.none,
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: const BorderSide(color: AppColors.primary400, width: 2),
    ),
    hintStyle: const TextStyle(
      fontFamily: 'Cairo',
      color: AppColors.gray500,
      fontSize: 15,
    ),
  ),
);
