#!/usr/bin/env python3
"""Demo script to showcase multilingual UI support.

This script demonstrates the i18n implementation for Google Photos Sync,
showing translations in English and Italian for all UI sections.

Run with: python demo_i18n.py
"""

from google_photos_sync.i18n import get_available_languages, get_translator


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def demo_language(lang_code: str, lang_name: str) -> None:
    """Demonstrate translations for a specific language."""
    print_section(f"{lang_name} ({lang_code})")

    t = get_translator(lang_code)

    # App info
    print(f"App Title:        {t('app.title')}")
    print(f"App Icon:         {t('app.icon')}")

    # Navigation
    print("\nNavigation:")
    print(f"  - {t('nav.home')}")
    print(f"  - {t('nav.compare')}")
    print(f"  - {t('nav.sync')}")
    print(f"  - {t('nav.settings')}")

    # Home page
    print("\nHome Page:")
    print(f"  Main Title:     {t('home.main_title')}")
    print(f"  Subtitle:       {t('home.subtitle')}")
    print(f"  What Is Title:  {t('home.what_is_title')}")
    print(f"  Features:       {t('home.features_title')}")
    print(f"  Getting Started: {t('home.getting_started_title')}")
    print(f"  Warnings:       {t('home.warnings_title')}")

    # Authentication
    print("\nAuthentication:")
    print(f"  Status:         {t('auth.status_title')}")
    print(f"  Source Account: {t('auth.source_account')}")
    print(f"  Target Account: {t('auth.target_account')}")
    print(f"  Not Signed In:  {t('auth.not_signed_in')}")

    # Compare page
    print("\nCompare Page:")
    print(f"  Title:          {t('compare.title')}")
    print(f"  Description:    {t('compare.description')}")
    print(f"  Compare Button: {t('compare.compare_button')}")

    # Sync page
    print("\nSync Page:")
    print(f"  Title:          {t('sync.title')}")
    print(f"  Description:    {t('sync.description')}")
    print(f"  Warning Title:  {t('sync.warning_title')}")
    print(f"  Confirmation:   {t('sync.confirmation_title')}")

    # Settings
    print("\nSettings:")
    print(f"  Title:          {t('settings.title')}")
    print(f"  Description:    {t('settings.description')}")
    print(f"  Save Button:    {t('settings.save_button')}")
    print(f"  Save Success:   {t('settings.save_success')}")

    # Language selector
    print("\nLanguage Selector:")
    print(f"  Label:          {t('language.selector_label')}")
    print(f"  English:        {t('language.english')}")
    print(f"  Italian:        {t('language.italian')}")

    # Footer
    print("\nFooter:")
    print(f"  Version:        {t('footer.version', version='1.0.0')}")
    print(f"  Documentation:  {t('footer.documentation')}")
    print(f"  Report Issue:   {t('footer.report_issue')}")


def main() -> None:
    """Main entry point for demo script."""
    print("\n" + "=" * 70)
    print("  Google Photos Sync - Multilingual UI Demo")
    print("=" * 70)

    # Show available languages
    languages = get_available_languages()
    print(f"\nAvailable Languages: {', '.join(languages)}")

    # Demo English
    demo_language("en", "English")

    # Demo Italian
    demo_language("it", "Italiano")

    # Show key features
    print_section("Key Features of i18n Implementation")
    print("✓ JSON-based translation files (easy to maintain)")
    print("✓ Dot notation for nested keys (app.title, nav.home)")
    print("✓ String formatting support (footer.version with {version})")
    print("✓ Fallback to English for missing translations")
    print("✓ Session-based language persistence in Streamlit")
    print("✓ Language selector component in sidebar")
    print("✓ Extensible architecture (easy to add more languages)")
    print("✓ Framework-agnostic translator service (reusable)")
    print("✓ Comprehensive test coverage (25 unit tests)")
    print("✓ Production-ready implementation")

    # Show how to add new language
    print_section("How to Add a New Language")
    print("1. Create new translation file: src/google_photos_sync/i18n/locales/XX.json")
    print("2. Copy structure from en.json")
    print("3. Translate all strings to new language")
    print("4. Add language flag and name to language_selector.py")
    print("5. Test with: get_translator('XX')")
    print("\nThat's it! The language will automatically appear in the selector.")

    print("\n" + "=" * 70)
    print("  Demo Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
