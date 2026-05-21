"""Tests for fill_utils.py - fill_utils.detect_long_ascii_block function."""
import pytest

import scripts.fill_utils as fill_utils


class TestDetectLongAsciiBlock:
    """Test suite for fill_utils.detect_long_ascii_block function."""

    def test_no_long_ascii_normal_chinese(self):
        """No issue detected for normal Chinese text without long ASCII runs."""
        text = "实验目的：掌握RTC时钟配置方法"
        result = fill_utils.detect_long_ascii_block(text)
        assert result["has_issue"] is False

    def test_no_long_ascii_with_spaces(self):
        """No issue detected when ASCII code has spaces (not compact)."""
        text = "GPIO_InitTypeDef GPIO_InitStructure; RCC_APB1PeriphClockCmd RCC_APB1Periph_ENABLE"
        result = fill_utils.detect_long_ascii_block(text)
        assert result["has_issue"] is False

    def test_detect_compact_c_code(self):
        """Compact C code without spaces should trigger detection."""
        text = "if(GPIO_ReadInputDataBit(GPIOA,GPIO_Pin_0)==0){delay_ms(20);if(GPIO_ReadInputDataBit(GPIOA,GPIO_Pin_0)==0){while(GPIO_ReadInputDataBit(GPIOA,GPIO_Pin_0)==0){WWDG_Set_Counter(0x7F);delay_ms(5);}WWDG_Set_Counter(0x7F);GPIO_SetBits(GPIOC,GPIO_Pin_4);}}"
        result = fill_utils.detect_long_ascii_block(text)
        assert result["has_issue"] is True
        assert len(result["segments"]) > 0

    def test_exclude_url(self):
        """URLs with protocol prefix should not be flagged as long ASCII."""
        text = "https://github.com/beihaizzz/labmate.skill/blob/main/README.md"
        result = fill_utils.detect_long_ascii_block(text)
        assert result["has_issue"] is False

    def test_exclude_filepath(self):
        """Filepaths with backslash separators should not be flagged."""
        text = "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
        result = fill_utils.detect_long_ascii_block(text)
        assert result["has_issue"] is False

    def test_threshold_boundary(self):
        """Boundary at 50 characters: 49=OK, 50=flagged."""
        text_49 = "A" * 49
        result_49 = fill_utils.detect_long_ascii_block(text_49)
        assert result_49["has_issue"] is False

        text_50 = "B" * 50
        result_50 = fill_utils.detect_long_ascii_block(text_50)
        assert result_50["has_issue"] is True

    def test_mixed_chinese_ascii(self):
        """Chinese text with short ASCII segment should not be flagged."""
        text = "在程序中写了if(x>0)这样的判断逻辑"
        result = fill_utils.detect_long_ascii_block(text)
        assert result["has_issue"] is False