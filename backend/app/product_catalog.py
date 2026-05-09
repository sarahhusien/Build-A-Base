from typing import Any

from sqlalchemy.orm import Session

from .compatibility import compatibility_profile
from .database import Product, SessionLocal


DEPTHS_ALL = "fair, light, medium, tan, deep, rich"
UNDERTONES_ALL = "cool, neutral, warm, olive"
SKIN_ALL = "dry, balanced, combination, oily"


PRODUCT_SEEDS: list[dict[str, Any]] = [
    # Drugstore foundations
    {"brand": "Maybelline", "name": "Fit Me Matte + Poreless Foundation", "product_type": "foundation", "finish": "natural matte", "coverage": "medium", "price_tier": "drugstore", "price": 11.99, "skin_type_match": "oily, combination, balanced", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "shine control, pore smoothing", "avoid_if": "very dry skin without rich prep"},
    {"brand": "Maybelline", "name": "Super Stay Active Wear Foundation", "product_type": "foundation", "finish": "matte", "coverage": "full", "price_tier": "drugstore", "price": 13.99, "skin_type_match": "oily, combination", "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "long wear, full glam", "avoid_if": "you prefer sheer flexible coverage"},
    {"brand": "L'Oreal Paris", "name": "True Match Super-Blendable Foundation", "product_type": "foundation", "finish": "natural", "coverage": "medium", "price_tier": "drugstore", "price": 14.99, "skin_type_match": SKIN_ALL, "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "undertone range, everyday wear", "avoid_if": "you want a very matte finish"},
    {"brand": "L'Oreal Paris", "name": "Infallible Fresh Wear Foundation", "product_type": "foundation", "finish": "natural matte", "coverage": "medium", "price_tier": "drugstore", "price": 16.99, "skin_type_match": "balanced, combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "lightweight long wear", "avoid_if": "you dislike fragrance"},
    {"brand": "NYX", "name": "Bare With Me Blur Tint Foundation", "product_type": "foundation", "finish": "soft matte", "coverage": "medium", "price_tier": "drugstore", "price": 14.0, "skin_type_match": "balanced, combination, oily", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "blurred texture, budget routines", "avoid_if": "you want a radiant finish"},
    {"brand": "e.l.f.", "name": "Soft Glam Satin Foundation", "product_type": "foundation", "finish": "satin", "coverage": "medium", "price_tier": "drugstore", "price": 8.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "soft everyday coverage", "avoid_if": "you need oil control"},
    {"brand": "e.l.f.", "name": "Flawless Finish Foundation", "product_type": "foundation", "finish": "semi-matte", "coverage": "medium", "price_tier": "drugstore", "price": 6.0, "skin_type_match": "balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "simple affordable base", "avoid_if": "you need a very wide shade range"},
    {"brand": "Wet n Wild", "name": "Photo Focus Foundation", "product_type": "foundation", "finish": "natural matte", "coverage": "medium", "price_tier": "drugstore", "price": 6.49, "skin_type_match": "balanced, combination, oily", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "photo-friendly matte looks", "avoid_if": "you are sensitive to strong product scent"},
    {"brand": "Revlon", "name": "ColorStay Makeup Combination/Oily", "product_type": "foundation", "finish": "matte", "coverage": "full", "price_tier": "drugstore", "price": 15.99, "skin_type_match": "combination, oily", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "long wear, oil control", "avoid_if": "your skin is dry or flaky"},
    {"brand": "Revlon", "name": "Illuminance Skin-Caring Foundation", "product_type": "foundation", "finish": "radiant", "coverage": "medium", "price_tier": "drugstore", "price": 17.99, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "comfortable glow", "avoid_if": "you want matte oil control"},
    {"brand": "Covergirl", "name": "TruBlend Matte Made Foundation", "product_type": "foundation", "finish": "matte", "coverage": "medium", "price_tier": "drugstore", "price": 12.99, "skin_type_match": "combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "matte shade range", "avoid_if": "you prefer skinlike glow"},
    {"brand": "Covergirl", "name": "Simply Ageless 3-in-1 Foundation", "product_type": "foundation", "finish": "natural", "coverage": "medium", "price_tier": "drugstore", "price": 17.99, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "smoother mature-skin look", "avoid_if": "you want ultra matte wear"},
    {"brand": "Milani", "name": "Conceal + Perfect 2-in-1 Foundation", "product_type": "foundation", "finish": "natural matte", "coverage": "full", "price_tier": "drugstore", "price": 12.99, "skin_type_match": "balanced, combination, oily", "undertone": "neutral, warm, olive", "shade_depth": "light, medium, tan, deep", "good_for": "fuller coverage, glam routines", "avoid_if": "you want a sheer base"},
    {"brand": "Juvia's Place", "name": "I Am Magic Foundation", "product_type": "foundation", "finish": "matte", "coverage": "full", "price_tier": "drugstore", "price": 20.0, "skin_type_match": "combination, oily", "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "deep shade range, full coverage", "avoid_if": "you want light coverage"},
    {"brand": "Black Radiance", "name": "Color Perfect Oil Free Foundation", "product_type": "foundation", "finish": "natural matte", "coverage": "medium", "price_tier": "drugstore", "price": 8.99, "skin_type_match": "balanced, combination, oily", "undertone": "neutral, warm, olive", "shade_depth": "tan, deep, rich", "good_for": "deeper drugstore shade options", "avoid_if": "you are fair or light depth"},

    # Mid-range foundations and tints
    {"brand": "The Ordinary", "name": "Serum Foundation", "product_type": "foundation", "finish": "natural", "coverage": "medium", "price_tier": "mid_range", "price": 24.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "affordable mid-range skinlike coverage", "avoid_if": "you want full matte wear"},
    {"brand": "Morphe", "name": "Filter Effect Soft-Focus Foundation", "product_type": "foundation", "finish": "soft-focus", "coverage": "medium", "price_tier": "mid_range", "price": 22.0, "skin_type_match": "balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "blurred mid-range coverage", "avoid_if": "you want very sheer tint"},
    {"brand": "Sephora Collection", "name": "Best Skin Ever Foundation", "product_type": "foundation", "finish": "natural", "coverage": "medium", "price_tier": "mid_range", "price": 22.0, "skin_type_match": SKIN_ALL, "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "flexible mid-range everyday foundation", "avoid_if": "you want luxury packaging"},
    {"brand": "Glossier", "name": "Perfecting Skin Tint", "product_type": "skin tint", "finish": "natural dewy", "coverage": "light", "price_tier": "mid_range", "price": 28.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "sheer clean-skin tint", "avoid_if": "you want coverage"},
    {"brand": "Ami Colé", "name": "Skin-Enhancing Tint", "product_type": "skin tint", "finish": "natural radiant", "coverage": "light", "price_tier": "mid_range", "price": 32.0, "skin_type_match": "dry, balanced, combination", "undertone": "neutral, warm, olive", "shade_depth": "medium, tan, deep, rich", "good_for": "melanin-rich tint range", "avoid_if": "you are fair depth"},

    # Premium foundations
    {"brand": "Fenty Beauty", "name": "Pro Filt'r Soft Matte Longwear Foundation", "product_type": "foundation", "finish": "soft matte", "coverage": "medium", "price_tier": "premium", "price": 40.0, "skin_type_match": "balanced, combination, oily", "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "wide shade range, soft matte wear", "avoid_if": "you want a dewy finish"},
    {"brand": "Fenty Beauty", "name": "Eaze Drop Blurring Skin Tint", "product_type": "foundation", "finish": "natural matte", "coverage": "light", "price_tier": "premium", "price": 36.0, "skin_type_match": "balanced, combination, oily", "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "blurred light coverage", "avoid_if": "you need full coverage"},
    {"brand": "NARS", "name": "Light Reflecting Foundation", "product_type": "foundation", "finish": "radiant", "coverage": "medium", "price_tier": "premium", "price": 52.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm, olive", "shade_depth": DEPTHS_ALL, "good_for": "skinlike radiance", "avoid_if": "you want matte oil control"},
    {"brand": "NARS", "name": "Natural Radiant Longwear Foundation", "product_type": "foundation", "finish": "radiant", "coverage": "full", "price_tier": "premium", "price": 52.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm, olive", "shade_depth": DEPTHS_ALL, "good_for": "glam radiant coverage", "avoid_if": "you dislike fuller coverage"},
    {"brand": "Armani Beauty", "name": "Luminous Silk Foundation", "product_type": "foundation", "finish": "natural radiant", "coverage": "medium", "price_tier": "premium", "price": 69.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm, olive", "shade_depth": DEPTHS_ALL, "good_for": "polished skinlike finish", "avoid_if": "you need strong oil control"},
    {"brand": "Dior", "name": "Forever Matte Foundation", "product_type": "foundation", "finish": "matte", "coverage": "full", "price_tier": "premium", "price": 60.0, "skin_type_match": "balanced, combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "premium matte long wear", "avoid_if": "skin feels very dry"},
    {"brand": "Dior", "name": "Forever Skin Glow Foundation", "product_type": "foundation", "finish": "radiant", "coverage": "medium", "price_tier": "premium", "price": 60.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "glowy premium base", "avoid_if": "you get oily quickly"},
    {"brand": "Charlotte Tilbury", "name": "Airbrush Flawless Foundation", "product_type": "foundation", "finish": "matte", "coverage": "full", "price_tier": "premium", "price": 49.0, "skin_type_match": "balanced, combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "full glam smoothing", "avoid_if": "you prefer sheer coverage"},
    {"brand": "Charlotte Tilbury", "name": "Beautiful Skin Foundation", "product_type": "foundation", "finish": "natural radiant", "coverage": "medium", "price_tier": "premium", "price": 49.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "healthy skin finish", "avoid_if": "you want flat matte"},
    {"brand": "Rare Beauty", "name": "Liquid Touch Weightless Foundation", "product_type": "foundation", "finish": "natural", "coverage": "medium", "price_tier": "premium", "price": 32.0, "skin_type_match": "balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "lightweight everyday coverage", "avoid_if": "you need heavy coverage"},
    {"brand": "Estée Lauder", "name": "Double Wear Stay-in-Place Foundation", "product_type": "foundation", "finish": "matte", "coverage": "full", "price_tier": "premium", "price": 52.0, "skin_type_match": "combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "very long wear", "avoid_if": "you want a flexible skin tint feel"},
    {"brand": "Pat McGrath Labs", "name": "Sublime Perfection Foundation", "product_type": "foundation", "finish": "natural satin", "coverage": "medium", "price_tier": "premium", "price": 69.0, "skin_type_match": "dry, balanced, combination", "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "luxury skinlike finish", "avoid_if": "you need matte oil control"},
    {"brand": "Hourglass", "name": "Ambient Soft Glow Foundation", "product_type": "foundation", "finish": "soft radiant", "coverage": "medium", "price_tier": "premium", "price": 58.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "soft-focus glow", "avoid_if": "you want full matte coverage"},
    {"brand": "Make Up For Ever", "name": "HD Skin Foundation", "product_type": "foundation", "finish": "natural", "coverage": "medium", "price_tier": "premium", "price": 47.0, "skin_type_match": "balanced, combination, oily", "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "photo-friendly realistic skin", "avoid_if": "you want very dewy finish"},
    {"brand": "Haus Labs", "name": "Triclone Skin Tech Foundation", "product_type": "foundation", "finish": "natural", "coverage": "medium", "price_tier": "premium", "price": 49.0, "skin_type_match": "dry, balanced, combination, oily", "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "flexible shade and undertone matching", "avoid_if": "you want ultra matte"},

    # Concealers
    {"brand": "Maybelline", "name": "Instant Age Rewind Eraser Concealer", "product_type": "concealer", "finish": "natural", "coverage": "medium", "price_tier": "drugstore", "price": 12.99, "skin_type_match": SKIN_ALL, "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "brightening, everyday concealing", "avoid_if": "you prefer a wand applicator"},
    {"brand": "e.l.f.", "name": "16HR Camo Concealer", "product_type": "concealer", "finish": "matte", "coverage": "full", "price_tier": "drugstore", "price": 8.0, "skin_type_match": "balanced, combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "full correction, long wear", "avoid_if": "under-eyes are very dry"},
    {"brand": "L.A. Girl", "name": "HD Pro Conceal", "product_type": "concealer", "finish": "natural", "coverage": "medium", "price_tier": "drugstore", "price": 5.99, "skin_type_match": SKIN_ALL, "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "budget correcting and shade variety", "avoid_if": "you dislike squeeze tubes"},
    {"brand": "NYX", "name": "Bare With Me Concealer Serum", "product_type": "concealer", "finish": "natural radiant", "coverage": "medium", "price_tier": "drugstore", "price": 12.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "hydrated under-eyes", "avoid_if": "you need full matte correction"},
    {"brand": "NARS", "name": "Radiant Creamy Concealer", "product_type": "concealer", "finish": "radiant", "coverage": "medium", "price_tier": "premium", "price": 32.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm, olive", "shade_depth": DEPTHS_ALL, "good_for": "radiant under-eye coverage", "avoid_if": "you want a matte concealer"},
    {"brand": "Tarte", "name": "Shape Tape Concealer", "product_type": "concealer", "finish": "matte", "coverage": "full", "price_tier": "premium", "price": 32.0, "skin_type_match": "balanced, combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "full coverage glam", "avoid_if": "your under-eyes crease easily"},
    {"brand": "Dior", "name": "Forever Skin Correct Concealer", "product_type": "concealer", "finish": "natural", "coverage": "full", "price_tier": "premium", "price": 40.0, "skin_type_match": SKIN_ALL, "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "premium flexible full coverage", "avoid_if": "you want drugstore pricing"},
    {"brand": "Kosas", "name": "Revealer Concealer", "product_type": "concealer", "finish": "natural radiant", "coverage": "medium", "price_tier": "premium", "price": 30.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm, olive", "shade_depth": DEPTHS_ALL, "good_for": "hydrated natural coverage", "avoid_if": "you want matte full coverage"},
    {"brand": "Rare Beauty", "name": "Liquid Touch Brightening Concealer", "product_type": "concealer", "finish": "natural", "coverage": "medium", "price_tier": "premium", "price": 24.0, "skin_type_match": "balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "lightweight spot concealing", "avoid_if": "you want maximum coverage"},
    {"brand": "Too Faced", "name": "Born This Way Super Coverage Concealer", "product_type": "concealer", "finish": "natural", "coverage": "full", "price_tier": "premium", "price": 36.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "full coverage without flat matte finish", "avoid_if": "you want a thin serum texture"},

    # Powders
    {"brand": "Maybelline", "name": "Fit Me Matte + Poreless Pressed Powder", "product_type": "pressed setting powder", "finish": "matte", "coverage": "light", "price_tier": "drugstore", "price": 11.99, "skin_type_match": "balanced, combination, oily", "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "touch-ups, shine control", "avoid_if": "you prefer loose powder only"},
    {"brand": "e.l.f.", "name": "Halo Glow Setting Powder", "product_type": "loose setting powder", "finish": "soft-focus", "coverage": "light", "price_tier": "drugstore", "price": 8.0, "skin_type_match": "dry, balanced, combination", "undertone": UNDERTONES_ALL, "shade_depth": "fair, light, medium, tan, deep", "good_for": "soft set without flatness", "avoid_if": "you need strong oil control"},
    {"brand": "Coty", "name": "Airspun Loose Face Powder", "product_type": "loose setting powder", "finish": "matte", "coverage": "light", "price_tier": "drugstore", "price": 9.99, "skin_type_match": "combination, oily", "undertone": "neutral", "shade_depth": "fair, light, medium", "good_for": "budget baking and setting", "avoid_if": "you dislike fragrance"},
    {"brand": "NYX", "name": "Can't Stop Won't Stop Mattifying Powder", "product_type": "pressed setting powder", "finish": "matte", "coverage": "light", "price_tier": "drugstore", "price": 10.0, "skin_type_match": "combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "oil control compact", "avoid_if": "your skin is dry"},
    {"brand": "Laura Mercier", "name": "Translucent Loose Setting Powder", "product_type": "loose setting powder", "finish": "soft matte", "coverage": "light", "price_tier": "premium", "price": 47.0, "skin_type_match": "balanced, combination, oily", "undertone": "neutral", "shade_depth": DEPTHS_ALL, "good_for": "premium soft-matte set", "avoid_if": "you want a luminous powder"},
    {"brand": "Charlotte Tilbury", "name": "Airbrush Flawless Finish Setting Powder", "product_type": "pressed setting powder", "finish": "soft-focus", "coverage": "light", "price_tier": "premium", "price": 48.0, "skin_type_match": "dry, balanced, combination", "undertone": "neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "smoothing touch-ups", "avoid_if": "you need a loose powder for baking"},
    {"brand": "Huda Beauty", "name": "Easy Bake Loose Baking & Setting Powder", "product_type": "loose setting powder", "finish": "matte", "coverage": "light", "price_tier": "premium", "price": 38.0, "skin_type_match": "combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "brightening and baking", "avoid_if": "you dislike a matte set"},
    {"brand": "Fenty Beauty", "name": "Pro Filt'r Instant Retouch Setting Powder", "product_type": "loose setting powder", "finish": "soft matte", "coverage": "light", "price_tier": "premium", "price": 36.0, "skin_type_match": "balanced, combination, oily", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "shade-flexible soft matte setting", "avoid_if": "you prefer pressed powder"},
    {"brand": "One/Size", "name": "Ultimate Blurring Setting Powder", "product_type": "loose setting powder", "finish": "matte", "coverage": "light", "price_tier": "premium", "price": 34.0, "skin_type_match": "combination, oily", "undertone": "neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "blurred glam set", "avoid_if": "you want glow"},
    {"brand": "Kosas", "name": "Cloud Set Baked Setting Powder", "product_type": "pressed setting powder", "finish": "natural", "coverage": "light", "price_tier": "premium", "price": 36.0, "skin_type_match": "dry, balanced, combination", "undertone": "neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "soft set for dry skin", "avoid_if": "you need strong mattifying"},

    # Skin tints and tinted moisturizers
    {"brand": "L'Oreal Paris", "name": "True Match Nude Hyaluronic Tinted Serum", "product_type": "skin tint", "finish": "natural radiant", "coverage": "light", "price_tier": "drugstore", "price": 19.99, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "hydrated light coverage", "avoid_if": "you need matte full coverage"},
    {"brand": "e.l.f.", "name": "Halo Glow Liquid Filter", "product_type": "skin tint", "finish": "glowy", "coverage": "light", "price_tier": "drugstore", "price": 14.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "radiance under or instead of foundation", "avoid_if": "you dislike glow"},
    {"brand": "Covergirl", "name": "Clean Fresh Skin Milk", "product_type": "skin tint", "finish": "dewy", "coverage": "light", "price_tier": "drugstore", "price": 11.99, "skin_type_match": "dry, balanced", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "bare-skin days", "avoid_if": "you need long wear"},
    {"brand": "Wet n Wild", "name": "Bare Focus Tinted Hydrator", "product_type": "skin tint", "finish": "natural", "coverage": "light", "price_tier": "drugstore", "price": 6.49, "skin_type_match": "dry, balanced, combination", "undertone": "neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "very affordable tint", "avoid_if": "you need broad undertone precision"},
    {"brand": "ColourPop", "name": "Pretty Fresh Tinted Moisturizer", "product_type": "skin tint", "finish": "natural radiant", "coverage": "light", "price_tier": "drugstore", "price": 16.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "fresh flexible tint", "avoid_if": "you want matte glam"},
    {"brand": "Fenty Beauty", "name": "Eaze Drop Blurring Skin Tint", "product_type": "skin tint", "finish": "natural matte", "coverage": "light", "price_tier": "premium", "price": 36.0, "skin_type_match": "balanced, combination, oily", "undertone": UNDERTONES_ALL, "shade_depth": DEPTHS_ALL, "good_for": "premium blurred tint", "avoid_if": "you want dewy glow"},
    {"brand": "Rare Beauty", "name": "Positive Light Tinted Moisturizer", "product_type": "skin tint", "finish": "natural radiant", "coverage": "light", "price_tier": "premium", "price": 30.0, "skin_type_match": "dry, balanced, combination", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "light flexible coverage", "avoid_if": "you need full coverage"},
    {"brand": "ILIA", "name": "Super Serum Skin Tint SPF 40", "product_type": "skin tint", "finish": "dewy", "coverage": "light", "price_tier": "premium", "price": 48.0, "skin_type_match": "dry, balanced", "undertone": "cool, neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "skincare-like glow", "avoid_if": "you dislike dewy finish"},
    {"brand": "Saie", "name": "Slip Tint Dewy Tinted Moisturizer", "product_type": "skin tint", "finish": "dewy", "coverage": "light", "price_tier": "premium", "price": 36.0, "skin_type_match": "dry, balanced", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "soft dewy everyday tint", "avoid_if": "you are very oily"},
    {"brand": "Tower 28", "name": "SunnyDays SPF 30 Tinted Sunscreen", "product_type": "skin tint", "finish": "natural", "coverage": "light", "price_tier": "premium", "price": 32.0, "skin_type_match": "dry, balanced, combination, sensitive", "undertone": "cool, neutral, warm", "shade_depth": "fair, light, medium, tan, deep", "good_for": "sensitive-skin friendly tint", "avoid_if": "you need full glam coverage"},

    # Routine support: primers, blush, bronzer/contour, setting sprays
    {"brand": "e.l.f.", "name": "Power Grip Primer", "product_type": "primer", "finish": "grippy", "coverage": "", "price_tier": "drugstore", "price": 10.0, "skin_type_match": "dry, balanced, combination", "undertone": "", "shade_depth": "", "good_for": "makeup grip and longer wear", "avoid_if": "you dislike tacky primers"},
    {"brand": "NYX", "name": "Marshmellow Smoothing Primer", "product_type": "primer", "finish": "smooth", "coverage": "", "price_tier": "drugstore", "price": 17.0, "skin_type_match": "dry, balanced, combination", "undertone": "", "shade_depth": "", "good_for": "smoothing patchy texture", "avoid_if": "you need strong oil control"},
    {"brand": "Milk Makeup", "name": "Hydro Grip Primer", "product_type": "primer", "finish": "grippy", "coverage": "", "price_tier": "premium", "price": 38.0, "skin_type_match": "dry, balanced, combination", "undertone": "", "shade_depth": "", "good_for": "premium grip under foundation", "avoid_if": "you dislike sticky primer feel"},
    {"brand": "Tatcha", "name": "The Silk Canvas Primer", "product_type": "primer", "finish": "smooth", "coverage": "", "price_tier": "premium", "price": 54.0, "skin_type_match": "balanced, combination, oily", "undertone": "", "shade_depth": "", "good_for": "luxury smoothing and pore blur", "avoid_if": "you prefer gel primers"},
    {"brand": "Milani", "name": "Baked Blush", "product_type": "powder blush", "finish": "satin", "coverage": "", "price_tier": "drugstore", "price": 10.99, "skin_type_match": "balanced, combination, oily", "undertone": "", "shade_depth": "", "good_for": "powder blush over set makeup", "avoid_if": "you want matte cheeks"},
    {"brand": "Maybelline", "name": "Fit Me Powder Blush", "product_type": "powder blush", "finish": "natural", "coverage": "", "price_tier": "drugstore", "price": 7.99, "skin_type_match": "balanced, combination, oily", "undertone": "", "shade_depth": "", "good_for": "soft affordable cheek color", "avoid_if": "you want bold pigment"},
    {"brand": "Dior", "name": "Rosy Glow Blush", "product_type": "powder blush", "finish": "radiant", "coverage": "", "price_tier": "premium", "price": 40.0, "skin_type_match": "dry, balanced, combination", "undertone": "", "shade_depth": "", "good_for": "premium bright cheek color", "avoid_if": "you want muted blush"},
    {"brand": "Pat McGrath Labs", "name": "Skin Fetish Divine Blush", "product_type": "powder blush", "finish": "satin", "coverage": "", "price_tier": "premium", "price": 39.0, "skin_type_match": "balanced, combination, oily", "undertone": "", "shade_depth": "", "good_for": "luxury buildable powder blush", "avoid_if": "you want drugstore pricing"},
    {"brand": "e.l.f.", "name": "Camo Liquid Blush", "product_type": "liquid blush", "finish": "natural", "coverage": "", "price_tier": "drugstore", "price": 7.0, "skin_type_match": SKIN_ALL, "undertone": "", "shade_depth": "", "good_for": "budget dewy cheek color", "avoid_if": "you prefer powder only"},
    {"brand": "NYX", "name": "Sweet Cheeks Soft Cheek Tint", "product_type": "liquid blush", "finish": "natural", "coverage": "", "price_tier": "drugstore", "price": 9.0, "skin_type_match": SKIN_ALL, "undertone": "", "shade_depth": "", "good_for": "affordable liquid blush", "avoid_if": "you want a powder finish"},
    {"brand": "Rare Beauty", "name": "Soft Pinch Liquid Blush", "product_type": "liquid blush", "finish": "natural", "coverage": "", "price_tier": "premium", "price": 25.0, "skin_type_match": SKIN_ALL, "undertone": "", "shade_depth": "", "good_for": "high-impact liquid blush", "avoid_if": "you dislike very pigmented blush"},
    {"brand": "Saie", "name": "Dew Blush", "product_type": "liquid blush", "finish": "dewy", "coverage": "", "price_tier": "premium", "price": 25.0, "skin_type_match": "dry, balanced, combination", "undertone": "", "shade_depth": "", "good_for": "soft dewy cheek color", "avoid_if": "you get oily quickly"},
    {"brand": "NYX", "name": "Buttermelt Bronzer", "product_type": "powder bronzer", "finish": "soft matte", "coverage": "", "price_tier": "drugstore", "price": 10.0, "skin_type_match": "balanced, combination, oily", "undertone": "neutral, warm", "shade_depth": "light, medium, tan, deep", "good_for": "smooth budget bronzing", "avoid_if": "you want shimmer"},
    {"brand": "Physicians Formula", "name": "Murumuru Butter Bronzer", "product_type": "powder bronzer", "finish": "satin", "coverage": "", "price_tier": "drugstore", "price": 16.49, "skin_type_match": "dry, balanced, combination", "undertone": "neutral, warm", "shade_depth": "fair, light, medium, tan", "good_for": "soft warm bronzing", "avoid_if": "you need very deep bronzer shades"},
    {"brand": "Fenty Beauty", "name": "Sun Stalk'r Instant Warmth Bronzer", "product_type": "powder bronzer", "finish": "matte", "coverage": "", "price_tier": "premium", "price": 35.0, "skin_type_match": "balanced, combination, oily", "undertone": "neutral, warm", "shade_depth": DEPTHS_ALL, "good_for": "premium powder bronzer range", "avoid_if": "you want shimmer"},
    {"brand": "Gucci", "name": "Poudre De Beauté Éclat Soleil Bronzing Powder", "product_type": "powder bronzer", "finish": "radiant", "coverage": "", "price_tier": "premium", "price": 65.0, "skin_type_match": "dry, balanced, combination", "undertone": "neutral, warm", "shade_depth": "light, medium, tan, deep", "good_for": "luxury radiant bronzing", "avoid_if": "you want matte"},
    {"brand": "e.l.f.", "name": "Halo Glow Contour Beauty Wand", "product_type": "liquid contour", "finish": "natural", "coverage": "", "price_tier": "drugstore", "price": 9.0, "skin_type_match": "dry, balanced, combination", "undertone": "neutral, warm", "shade_depth": "light, medium, tan, deep", "good_for": "easy liquid contour", "avoid_if": "you prefer powder sculpting"},
    {"brand": "NYX", "name": "Wonder Stick Cream Contour", "product_type": "cream contour", "finish": "natural matte", "coverage": "", "price_tier": "drugstore", "price": 14.0, "skin_type_match": "balanced, combination", "undertone": "neutral, warm", "shade_depth": "light, medium, tan, deep", "good_for": "budget cream sculpting", "avoid_if": "you dislike stick formulas"},
    {"brand": "Fenty Beauty", "name": "Match Stix Matte Contour Skinstick", "product_type": "cream contour", "finish": "matte", "coverage": "", "price_tier": "premium", "price": 32.0, "skin_type_match": "balanced, combination, oily", "undertone": "neutral, warm, olive", "shade_depth": DEPTHS_ALL, "good_for": "premium cream contour range", "avoid_if": "you want a liquid wand"},
    {"brand": "Charlotte Tilbury", "name": "Hollywood Contour Wand", "product_type": "liquid contour", "finish": "natural", "coverage": "", "price_tier": "premium", "price": 42.0, "skin_type_match": "dry, balanced, combination", "undertone": "neutral, warm", "shade_depth": "light, medium, tan, deep", "good_for": "soft premium liquid sculpting", "avoid_if": "you want matte stick contour"},
    {"brand": "Milani", "name": "Make It Last Original Setting Spray", "product_type": "setting spray", "finish": "natural", "coverage": "", "price_tier": "drugstore", "price": 10.99, "skin_type_match": SKIN_ALL, "undertone": "", "shade_depth": "", "good_for": "budget longer wear", "avoid_if": "you want a very matte spray"},
    {"brand": "NYX", "name": "Matte Finish Makeup Setting Spray", "product_type": "setting spray", "finish": "matte", "coverage": "", "price_tier": "drugstore", "price": 10.0, "skin_type_match": "combination, oily", "undertone": "", "shade_depth": "", "good_for": "drugstore shine control", "avoid_if": "your skin is very dry"},
    {"brand": "Urban Decay", "name": "All Nighter Setting Spray", "product_type": "setting spray", "finish": "natural", "coverage": "", "price_tier": "premium", "price": 36.0, "skin_type_match": SKIN_ALL, "undertone": "", "shade_depth": "", "good_for": "premium long wear", "avoid_if": "you avoid alcohol-based sprays"},
    {"brand": "Charlotte Tilbury", "name": "Airbrush Flawless Setting Spray", "product_type": "setting spray", "finish": "natural", "coverage": "", "price_tier": "premium", "price": 38.0, "skin_type_match": SKIN_ALL, "undertone": "", "shade_depth": "", "good_for": "soft-focus luxury setting", "avoid_if": "you want a matte spray"},
]


PRICE_TIER_ORDER = {"drugstore": 0, "mid_range": 1, "premium": 2}
FALLBACK_PRODUCT_IMAGE = "/product-images/fallback-product.jpg"

PRODUCT_IMAGE_URLS = {
    "16HR Camo Concealer": "https://media.ulta.com/i/ulta/2541153?w=640&h=640",
    "Airbrush Flawless Foundation": "https://media.ulta.com/i/ulta/2601573?w=640&h=640",
    "Buttermelt Bronzer": "https://media.ulta.com/i/ulta/2623793?w=640&h=640",
    "Camo Liquid Blush": "https://media.ulta.com/i/ulta/2617738?w=640&h=640",
    "Conceal + Perfect 2-in-1 Foundation": "https://media.ulta.com/i/ulta/2519968?w=640&h=640",
    "ColorStay Makeup Combination/Oily": "https://d3t32hsnjxo7q6.cloudfront.net/i/844f8a41bfd962e75295db3b75ad3167_ra,w158,h184_pa,w158,h184.jpeg",
    "Dior Rosy Glow Blush": "https://media.ulta.com/i/ulta/2639599?w=640&h=640",
    "Fit Me Matte + Poreless Foundation": "https://d3t32hsnjxo7q6.cloudfront.net/i/257993e12625cc45a72ec03636ffa5c5_ra,w158,h184_pa,w158,h184.jpg",
    "Fit Me Matte + Poreless Pressed Powder": "https://media.ulta.com/i/ulta/2282887?w=640&h=640",
    "Fit Me Powder Blush": "https://d3t32hsnjxo7q6.cloudfront.net/i/53d5f825461117c0d96946e1029510b0_ra,w158,h184_pa,w158,h184.png",
    "Flawless Finish Foundation": "https://d3t32hsnjxo7q6.cloudfront.net/i/f930f8fcd14f31ce1700faf24c4606f5_ra,w158,h184_pa,w158,h184.jpeg",
    "Halo Glow Liquid Filter": "https://media.ulta.com/i/ulta/2604929?w=640&h=640",
    "I Am Magic Foundation": "https://media.ulta.com/i/ulta/2551761?w=640&h=640",
    "Instant Age Rewind Eraser Concealer": "https://www.maybelline.com/-/media/project/loreal/brand-sites/mny/americas/us/face-makeup/concealer/instant-age-rewind-eraser-dark-circles-concealer-treatment/maybelline-face-instant-age-rewind-eraser-concealer-packshot-sand.jpg?rev=3c118fabf9374ae7a9ebd1aa2bfbac84",
    "Make It Last Original Setting Spray": "https://media.ulta.com/i/ulta/2519996?w=640&h=640",
    "Matte Finish Makeup Setting Spray": "https://media.ulta.com/i/ulta/2254931?w=640&h=640",
    "Perfecting Skin Tint": "https://static-assets.glossier.com/production/spree/images/attachments/000/000/726/portrait_normal/PST_Carousel_02-compressor.jpg?1470088244",
    "Power Grip Primer": "https://media.ulta.com/i/ulta/2591795?w=640&h=640",
    "Pro Filt'r Soft Matte Longwear Foundation": "https://media.ulta.com/i/ulta/2592533?w=640&h=640",
    "Shape Tape Concealer": "https://media.ulta.com/i/ulta/2304918?w=640&h=640",
    "Simply Ageless 3-in-1 Foundation": "https://d3t32hsnjxo7q6.cloudfront.net/i/fd47eaa9241a010e48fc32cf4611d772_ra,w158,h184_pa,w158,h184.png",
    "Soft Pinch Liquid Blush": "https://media.ulta.com/i/ulta/2597482?w=640&h=640",
    "True Match Super-Blendable Foundation": "https://d3t32hsnjxo7q6.cloudfront.net/i/c71a2c6a4f7d41ceb60f068780bcfba5_ra,w158,h184_pa,w158,h184.jpeg",
    "All Nighter Setting Spray": "https://media.ulta.com/i/ulta/2642048?w=640&h=640",
    "Match Stix Matte Contour Skinstick": "https://media.ulta.com/i/ulta/2592538?w=640&h=640",
    "Baked Blush": "https://d3t32hsnjxo7q6.cloudfront.net/i/4ae353dcae46e9b97c4915566fc9190a_ra,w158,h184_pa,w158,h184.png",
}

BRAND_CATEGORY_IMAGE_URLS = {
    ("Maybelline", "pressed setting powder"): "https://media.ulta.com/i/ulta/2282887?w=640&h=640",
    ("NYX", "powder bronzer"): "https://media.ulta.com/i/ulta/2623793?w=640&h=640",
    ("NYX", "setting spray"): "https://media.ulta.com/i/ulta/2254931?w=640&h=640",
    ("e.l.f.", "primer"): "https://media.ulta.com/i/ulta/2591795?w=640&h=640",
    ("e.l.f.", "liquid blush"): "https://media.ulta.com/i/ulta/2617738?w=640&h=640",
    ("Revlon", "foundation"): "https://media.ulta.com/i/ulta/2222382?w=640&h=640",
    ("Milani", "foundation"): "https://media.ulta.com/i/ulta/2519968?w=640&h=640",
    ("Milani", "setting spray"): "https://media.ulta.com/i/ulta/2519996?w=640&h=640",
    ("Fenty Beauty", "foundation"): "https://media.ulta.com/i/ulta/2592533?w=640&h=640",
    ("Dior", "powder blush"): "https://media.ulta.com/i/ulta/2639599?w=640&h=640",
    ("Charlotte Tilbury", "foundation"): "https://media.ulta.com/i/ulta/2601573?w=640&h=640",
    ("Rare Beauty", "liquid blush"): "https://media.ulta.com/i/ulta/2597482?w=640&h=640",
    ("Tarte", "concealer"): "https://media.ulta.com/i/ulta/2304918?w=640&h=640",
    ("Urban Decay", "setting spray"): "https://media.ulta.com/i/ulta/2642048?w=640&h=640",
}


def recommend_products(
    category: str | None = None,
    skin_type: str | None = None,
    undertone: str | None = None,
    depth: str | None = None,
    budget: str | None = None,
    finish_preference: str | None = None,
    limit: int = 4,
) -> list[dict[str, str]]:
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return recommend_products_from_rows(
            products,
            category=category,
            skin_type=skin_type,
            undertone=undertone,
            depth=depth,
            budget=budget,
            finish_preference=finish_preference,
            limit=limit,
        )
    finally:
        db.close()


def recommend_products_from_rows(
    products: list[Product],
    category: str | None = None,
    skin_type: str | None = None,
    undertone: str | None = None,
    depth: str | None = None,
    budget: str | None = None,
    finish_preference: str | None = None,
    coverage: str | None = None,
    limit: int = 4,
) -> list[dict[str, str]]:
    filtered, fallback_reason = filter_products(
        products,
        category=category,
        skin_type=skin_type,
        undertone=undertone,
        depth=depth,
        budget=budget,
        finish_preference=finish_preference,
        coverage=coverage,
    )
    scored = sorted(
        [(_score_product(product, skin_type, undertone, depth, finish_preference, coverage), product) for product in filtered],
        key=lambda item: item[0],
        reverse=True,
    )
    return [_product_to_dict(product, skin_type, undertone, depth, fallback_reason, score) for score, product in scored[:limit]]


def filter_products(
    products: list[Product],
    category: str | None = None,
    skin_type: str | None = None,
    undertone: str | None = None,
    depth: str | None = None,
    budget: str | None = None,
    finish_preference: str | None = None,
    coverage: str | None = None,
) -> tuple[list[Product], str]:
    requested_tier = _normalize_tier(budget)
    category_matches = [product for product in products if not category or _matches_category(product, category)]

    tier_matches = [product for product in category_matches if product.price_tier == requested_tier]
    fallback_reason = ""
    if not tier_matches:
        tier_matches = category_matches
        fallback_reason = f"No exact {requested_tier} match was found, so the closest available tier was used."

    strict = _apply_profile_filters(tier_matches, skin_type, undertone, depth, finish_preference, coverage, strict=True)
    if strict:
        return strict, fallback_reason

    relaxed = _apply_profile_filters(tier_matches, skin_type, undertone, depth, finish_preference, coverage, strict=False)
    if relaxed:
        return relaxed, fallback_reason or "No exact profile match was found, so nearby formula matches were included."

    return tier_matches, fallback_reason or "No exact profile match was found, so products from the requested tier and type were ranked."


def seed_products(db: Session) -> None:
    existing_names = {name for (name,) in db.query(Product.name).all()}
    seed_names = {item["name"] for item in PRODUCT_SEEDS}
    if seed_names.issubset(existing_names) and db.query(Product).count() >= len(PRODUCT_SEEDS):
        _refresh_product_photos(db)
        return

    db.query(Product).delete()
    for item in PRODUCT_SEEDS:
        db.add(
            Product(
                brand=item["brand"],
                name=item["name"],
                product_type=item["product_type"],
                shade_name=item.get("shade_name", "varies"),
                shade_depth=item.get("shade_depth", item.get("depth", "")),
                depth=item.get("shade_depth", item.get("depth", "")),
                undertone=item.get("undertone", ""),
                skin_type_match=item.get("skin_type_match", ""),
                coverage=item.get("coverage", ""),
                finish=item.get("finish", ""),
                price_tier=item.get("price_tier", "drugstore"),
                price=float(item.get("price", 0.0)),
                good_for=item.get("good_for", ""),
                avoid_if=item.get("avoid_if", ""),
                notes=item.get("notes") or item.get("good_for", ""),
                image_url=_image_url_for_seed(item),
                shopping_link="",
                formula_base=item.get("formula_base") or _formula_base_for_seed(item),
                best_for=item.get("best_for") or item.get("skin_type_match", ""),
                avoid_pairing_with=item.get("avoid_pairing_with") or _avoid_pairing_for_seed(item),
                compatibility_notes=item.get("compatibility_notes") or _compatibility_notes_for_seed(item),
            )
        )
    db.commit()


def _refresh_product_photos(db: Session) -> None:
    changed = False
    by_name = {item["name"]: item for item in PRODUCT_SEEDS}
    for product in db.query(Product).all():
        seed = by_name.get(product.name)
        next_url = _image_url_for_seed(seed) if seed else FALLBACK_PRODUCT_IMAGE
        if product.image_url != next_url:
            product.image_url = next_url
            changed = True
        if seed and not product.formula_base:
            product.formula_base = _formula_base_for_seed(seed)
            changed = True
        if seed and not product.best_for:
            product.best_for = seed.get("skin_type_match", "")
            changed = True
        if seed and not product.avoid_pairing_with:
            product.avoid_pairing_with = _avoid_pairing_for_seed(seed)
            changed = True
        if seed and not product.compatibility_notes:
            product.compatibility_notes = _compatibility_notes_for_seed(seed)
            changed = True
    if changed:
        db.commit()


def _image_url_for_seed(item: dict[str, Any]) -> str:
    if item.get("image_url"):
        return item["image_url"]
    if item["name"] in PRODUCT_IMAGE_URLS:
        return _local_product_image_path(item)
    return FALLBACK_PRODUCT_IMAGE


def _local_product_image_path(item: dict[str, Any]) -> str:
    slug = _slug(f"{item['brand']} {item['name']}")
    return f"/product-images/{slug}.png"


def _slug(value: str) -> str:
    slug = []
    for character in value.lower():
        if character.isalnum():
            slug.append(character)
        elif slug and slug[-1] != "-":
            slug.append("-")
    return "".join(slug).strip("-")


def _formula_base_for_seed(item: dict[str, Any]) -> str:
    text = " ".join(str(item.get(key, "")) for key in ["product_type", "finish", "good_for", "notes"]).lower()
    if "powder" in text:
        return "powder"
    if "primer" in text and any(word in text for word in ["hydro", "hydrating", "grip", "dewy"]):
        return "water-based"
    if any(word in text for word in ["matte", "blur", "pore", "soft-focus", "long wear", "longwear"]):
        return "silicone-heavy"
    if any(word in text for word in ["dewy", "radiant", "glow", "hydrated"]):
        return "water-based"
    return "balanced"


def _avoid_pairing_for_seed(item: dict[str, Any]) -> str:
    formula = _formula_base_for_seed(item)
    product_type = item.get("product_type", "")
    finish = item.get("finish", "")
    if product_type == "primer" and formula == "water-based":
        return "silicone-heavy foundation applied immediately"
    if "powder" in product_type:
        return "heavy powder layering on dry or flaky skin"
    if "matte" in finish:
        return "dry, flaky skin without hydrating prep"
    return ""


def _compatibility_notes_for_seed(item: dict[str, Any]) -> str:
    profile = compatibility_profile({**item, "category": item.get("product_type", "")})
    return f"{profile['formula_base']} formula behavior; best for {item.get('skin_type_match', 'varied skin types')}."


def _apply_profile_filters(
    products: list[Product],
    skin_type: str | None,
    undertone: str | None,
    depth: str | None,
    finish_preference: str | None,
    coverage: str | None,
    strict: bool,
) -> list[Product]:
    filtered = products
    if skin_type:
        filtered = [product for product in filtered if skin_type.lower() in product.skin_type_match.lower()]
    if undertone:
        filtered = [product for product in filtered if undertone.lower() in product.undertone.lower() or not product.undertone]
    if depth:
        filtered = [product for product in filtered if depth.lower() in product.shade_depth.lower() or not product.shade_depth]
    if coverage:
        filtered = [product for product in filtered if _coverage_match(product.coverage, coverage, strict)]
    if finish_preference and strict:
        finish_words = _finish_words(finish_preference)
        if finish_words:
            filtered = [product for product in filtered if any(word in product.finish.lower() for word in finish_words)]
    return filtered


def _score_product(
    product: Product,
    skin_type: str | None,
    undertone: str | None,
    depth: str | None,
    finish_preference: str | None,
    coverage: str | None,
) -> int:
    score = 60
    matched = _matched_answers(product, skin_type, undertone, depth, finish_preference, coverage)
    score += len(matched) * 6
    if coverage and _coverage_match(product.coverage, coverage, strict=True):
        score += 8
    if finish_preference and any(word in product.finish.lower() for word in _finish_words(finish_preference)):
        score += 8
    if product.good_for:
        score += 2
    return min(score, 98)


def _product_to_dict(
    product: Product,
    skin_type: str | None,
    undertone: str | None,
    depth: str | None,
    fallback_reason: str,
    score: int,
) -> dict[str, str]:
    downside = product.avoid_if or "No major downside based on this profile."
    if fallback_reason:
        downside = f"{fallback_reason} {downside}"
    return {
        "id": str(product.id),
        "name": product.name,
        "brand": product.brand,
        "category": product.product_type,
        "shade_name": product.shade_name,
        "budget": product.price_tier,
        "price_tier": product.price_tier,
        "finish": product.finish,
        "coverage": product.coverage,
        "why": product.good_for or product.notes,
        "shade_note": _shade_note(product, undertone, depth),
        "typical_price": f"${product.price:.2f}" if product.price else "Price varies",
        "image_url": product.image_url,
        "price_note": "Typical price; live prices and availability can change.",
        "shopping_link": product.shopping_link,
        "source": "sqlite_products",
        "good_for": product.good_for,
        "avoid_if": product.avoid_if,
        "possible_downside": downside,
        "matched_answers": ", ".join(_matched_answers(product, skin_type, undertone, depth, None, None)),
        "match_percentage": str(score),
        "why_recommended": product.good_for or product.notes,
        "formula_base": product.formula_base,
        "best_for": product.best_for,
        "avoid_pairing_with": product.avoid_pairing_with,
        "compatibility_notes": product.compatibility_notes,
    }


def _matches_category(product: Product, category: str) -> bool:
    product_type = product.product_type.lower()
    category = category.lower()
    return product_type == category or category in product_type


def _coverage_match(product_coverage: str, requested: str, strict: bool) -> bool:
    requested = requested.lower()
    product_coverage = product_coverage.lower()
    if not requested:
        return True
    if requested in product_coverage:
        return True
    if not strict and requested == "full" and product_coverage in {"medium", "buildable"}:
        return True
    if not strict and requested == "medium" and product_coverage in {"light", "full"}:
        return True
    return False


def _finish_words(finish_preference: str | None) -> list[str]:
    text = (finish_preference or "").lower()
    words = []
    for word in ["matte", "radiant", "glow", "glowy", "dewy", "natural", "satin", "soft-focus"]:
        if word in text:
            words.append("glow" if word == "glowy" else word)
    return words


def _matched_answers(
    product: Product,
    skin_type: str | None,
    undertone: str | None,
    depth: str | None,
    finish_preference: str | None,
    coverage: str | None,
) -> list[str]:
    matches = []
    if skin_type and skin_type.lower() in product.skin_type_match.lower():
        matches.append(f"skin type: {skin_type}")
    if undertone and undertone.lower() in product.undertone.lower():
        matches.append(f"undertone: {undertone}")
    if depth and depth.lower() in product.shade_depth.lower():
        matches.append(f"depth: {depth}")
    if finish_preference and any(word in product.finish.lower() for word in _finish_words(finish_preference)):
        matches.append(f"finish: {product.finish}")
    if coverage and coverage.lower() in product.coverage.lower():
        matches.append(f"coverage: {coverage}")
    return matches


def _shade_note(product: Product, undertone: str | None, depth: str | None) -> str:
    if product.product_type not in {"foundation", "skin tint", "concealer"}:
        return "No exact shade needed."
    return f"Start with the {depth or 'your depth'} range and {undertone or 'your'} undertone; swatch at the jawline in daylight."


def _normalize_tier(value: str | None) -> str:
    value = (value or "mid_range").lower()
    if value in {"moderate", "mid", "mid-range", "mid range"}:
        return "mid_range"
    if value in PRICE_TIER_ORDER:
        return value
    return "mid_range"
