import json
import os
import shutil
from bs4 import BeautifulSoup


# ==============================================================================
# BOILERPLATE TEMPLATES
# ==============================================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Timeline Website</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
    <!-- General Website Stylesheet -->
    <link rel="stylesheet" href="style/style.css">

    <!-- Custom Timeline Stylesheet -->
    <link rel="stylesheet" href="style/timeline_stylesheet.css">

    <!-- Vis Timeline Standalone Script -->
    <script src="https://visjs.github.io/vis-timeline/standalone/umd/vis-timeline-graph2d.min.js"></script>
</head>

<body>

    <main class="content">
        <!-- Overlay Navigation Buttons -->
        <button id="prevBtn" class="nav-btn left-btn" aria-label="Previous Slide">&#10094;</button>
        <button id="nextBtn" class="nav-btn right-btn" aria-label="Next Slide">&#10095;</button>
    </main>    

    <!-- Bottom timeline container -->    
    <div id="visualizer"></div>        

    <!-- Script file -->
    <script src="script.js"></script>
</body>
</html>
"""

CSS_TEMPLATE = """/* ==========================================================================
   1. BASE RESET & VIEWPORT CONTAINER
   ========================================================================== */
html, body {
  margin: 0;
  padding: 0;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  font-family: Arial, sans-serif;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
}

main.content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
  min-height: 0;
  width: 100%;
}

/* ==========================================================================
   2. SLIDE LAYOUTS & FULL-WIDTH BACKGROUNDS
   ========================================================================== */
.timeline_item, .title_item {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  gap: 40px;
  padding: 40px 80px;
  box-sizing: border-box;
  opacity: 0;
  visibility: hidden;
  position: absolute;
  top: 0;
  left: 0;
  transform: translateY(15px);
  transition: opacity 0.3s ease-in-out, transform 0.3s ease-in-out, visibility 0.3s;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.title_item, .timeline_item.no-media {
  justify-content: center;
  text-align: center;
}

.title_content, .timeline_item.no-media .left_content {
  max-width: 1200px;
  width: 85%;
  padding: 50px;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  box-sizing: border-box;
  margin: 0 auto;
  align-items: center;
}

.timeline_item.active, .title_item.active {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

/* ==========================================================================
   3. MEDIA & CONTENT COLUMNS (DYNAMICALLY BALANCED)
   ========================================================================== */
.left_content {
  flex: 1 1 50%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  max-width: 50%;
  width: 100%;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  box-sizing: border-box;
}

.right_content {
  flex: 1 1 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  max-width: 50%;
  height: 100%;
  box-sizing: border-box;
}

.right_content img {
  max-width: 100%;
  max-height: 72vh;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 6px;
}

/* ==========================================================================
   4. OVERLAY NAVIGATION BUTTONS
   ========================================================================== */
.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  background: rgba(0, 0, 0, 0.4);
  color: #ffffff;
  border: none;
  font-size: 1.8rem;
  padding: 16px 14px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s ease, opacity 0.2s ease;
  user-select: none;
}

.nav-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}

.left-btn {
  left: 15px;
}

.right-btn {
  right: 15px;
}

/* ==========================================================================
   5. DYNAMIC GENERATED OVERRIDES
   ========================================================================== */
/* DYNAMIC STYLES START */
/* DYNAMIC STYLES END */
"""

JS_TEMPLATE = """var currentSlideIndex = 0;

function setActiveSlide(targetId) {
  var allSlides = document.querySelectorAll(".title_item, .timeline_item");
  allSlides.forEach(function(slide, index) {
    if (slide.id === targetId) {
      slide.classList.add("active");
      currentSlideIndex = index;
    } else {
      slide.classList.remove("active");
    }
  });
}

function navigateSlide(direction) {
  if (typeof rawItems === "undefined" || !rawItems || rawItems.length === 0) return;
  
  var newIndex = currentSlideIndex + direction;
  if (newIndex >= 0 && newIndex < rawItems.length) {
    var targetId = rawItems[newIndex].id;
    setActiveSlide(targetId);
    
    if (window.visTimeline) {
      window.visTimeline.setSelection(targetId);
      window.visTimeline.focus(targetId, { animation: { duration: 300, easing: 'easeInOutQuad' } });
    }
  }
}

document.addEventListener("DOMContentLoaded", function() {
  var container = document.getElementById("visualizer");

  var prevBtn = document.getElementById("prevBtn");
  var nextBtn = document.getElementById("nextBtn");

  if (prevBtn) prevBtn.addEventListener("click", function() { navigateSlide(-1); });
  if (nextBtn) nextBtn.addEventListener("click", function() { navigateSlide(1); });

  document.addEventListener("keydown", function(e) {
    if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      navigateSlide(-1);
    } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      navigateSlide(1);
    }
  });

  if (typeof rawItems === "undefined" || !rawItems) return;

  var items = new vis.DataSet(rawItems);

  var options = {
    editable: false,
    selectable: true,
    height: "100%",
    margin: {
      item: 12
    },
    stack: true,
    zoomMin: 1000 * 60 * 60 * 24 * 10,
    zoomMax: 1000 * 60 * 60 * 24 * 365 * 50,
    template: function(item, element, data) {
      return '<div class="custom-timeline-item">' +
               '<span class="item-label">' + (item.content || '') + '</span>' +
             '</div>';
    }
  };

  var timeline = new vis.Timeline(container, items, options);
  window.visTimeline = timeline;

  timeline.fit();

  if (rawItems.length > 0) {
    setActiveSlide(rawItems[0].id);
    timeline.setSelection(rawItems[0].id);
    timeline.focus(rawItems[0].id, { animation: false });
  }

  window.addEventListener("resize", function() {
    timeline.redraw();
  });

  timeline.on("select", function(properties) {
    if (properties.items.length > 0) {
      setActiveSlide(properties.items[0]);
      window.visTimeline.focus(properties.items[0], { animation: { duration: 300, easing: 'easeInOutQuad' } });
    }
  });
});
"""

# ==============================================================================
# ASSET & DATA HELPERS
# ==============================================================================

def hex_to_rgba(hex_color: str, opacity: float = 0.80) -> str:
    if not hex_color:
        hex_color = "#000000"

    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    if len(hex_color) != 6:
        return f"rgba(0, 0, 0, {opacity})"

    try:
        opacity_val = max(0.0, min(1.0, float(opacity)))
    except (ValueError, TypeError):
        opacity_val = 0.80

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return f"rgba({r}, {g}, {b}, {opacity_val})"


def process_and_copy_image(original_path: str, imgs_dir: str) -> str:
    if not original_path or not os.path.isfile(original_path):
        return ""

    filename = os.path.basename(original_path)
    destination_path = os.path.join(imgs_dir, filename)

    try:
        shutil.copy2(original_path, destination_path)
        return f"imgs/{filename}"
    except Exception as e:
        print(f"Error copying asset {original_path}: {e}")
        return ""


def parse_data(data: list, imgs_dir: str, global_block_opacity: float = None) -> list:
    valid_events = []
    counter = 0

    for elm in data:
        if not isinstance(elm, dict):
            continue

        headline = elm.get("headline", "").strip()
        body_text = elm.get("text_body", "").strip()
        start_date = elm.get("start_date", "").strip()

        if not headline and not body_text and not start_date:
            continue

        style_data = elm.get("style_data", {})

        if "block_color" not in style_data:
            style_data["block_color"] = "#000000"

        if "block_opacity" not in style_data:
            style_data["block_opacity"] = 0.80

        if "bg_image_overlay" not in style_data:
            style_data["bg_image_overlay"] = 0.40

        if global_block_opacity is not None:
            style_data["block_opacity"] = global_block_opacity

        bg_img_src = style_data.get("bg_image_path", "")
        media_img_src = style_data.get("media_image_path", "")

        style_data["bg_image_relative"] = process_and_copy_image(bg_img_src, imgs_dir)
        style_data["media_image_relative"] = process_and_copy_image(media_img_src, imgs_dir)

        event_type = "timeline" if start_date else "title"
        element_id = f"{event_type}_{counter}"

        valid_events.append({"id": element_id, "type": event_type, "data": elm})
        counter += 1

    return valid_events


def create_html_structure(events: list) -> str:
    text = ""

    for item in events:
        element_id = item["id"]
        event_type = item["type"]
        event_dict = item["data"]

        headline = event_dict.get("headline", "")
        body_text = event_dict.get("text_body", "")
        style_data = event_dict.get("style_data", {})
        media_img = style_data.get("media_image_relative", "")

        if event_type == "title":
            text += f"""
    <div id="{element_id}" class="title_item">
        <div class="title_content">
            <h3>{headline}</h3>
            <p>{body_text}</p>
        </div>
    </div>
"""
        elif event_type == "timeline":
            if media_img:
                img_tag = f'<img src="{media_img}" alt="{headline}">'
                text += f"""
    <div id="{element_id}" class="timeline_item">
        <div class="left_content">
            <h3>{headline}</h3>
            <p>{body_text}</p>
        </div>
        <div class="right_content">
            {img_tag}
        </div>
    </div>
"""
            else:
                text += f"""
    <div id="{element_id}" class="timeline_item no-media">
        <div class="left_content">
            <h3>{headline}</h3>
            <p>{body_text}</p>
        </div>
    </div>
"""

    return text


def create_css_structure(events: list) -> str:
    css_rules = []

    for item in events:
        element_id = item["id"]
        event_dict = item["data"]
        style_data = event_dict.get("style_data", {})

        bg_type = style_data.get("bg_type", "color")
        bg_color = style_data.get("bg_color", "#ffffff")
        bg_img_rel = style_data.get("bg_image_relative", "")

        try:
            bg_overlay_val = max(0.0, min(1.0, float(style_data.get("bg_image_overlay", 0.40))))
        except (ValueError, TypeError):
            bg_overlay_val = 0.40

        overlay_rgba = f"rgba(0, 0, 0, {bg_overlay_val})"

        block_color = style_data.get("block_color", "#000000")
        block_opacity = style_data.get("block_opacity", 0.80)

        block_rgba = hex_to_rgba(block_color, block_opacity)

        heading_font = style_data.get("heading_font", "Arial")
        heading_size = style_data.get("heading_size", 24)
        heading_color = style_data.get("heading_color", "#ffffff")

        body_font = style_data.get("body_font", "Arial")
        body_size = style_data.get("body_size", 14)
        body_color = style_data.get("body_color", "#cccccc")

        if bg_type == "image" and bg_img_rel:
            css_bg_img_path = f"../{bg_img_rel}"
            bg_rule = f"background-image: linear-gradient({overlay_rgba}, {overlay_rgba}), url('{css_bg_img_path}');"
        else:
            bg_rule = f"background-color: {bg_color};"

        rule_block = f"""
#{element_id} {{
    {bg_rule}
}}
#{element_id} .left_content, #{element_id} .title_content {{
    background-color: {block_rgba};
}}
#{element_id} h3 {{
    font-family: '{heading_font}', sans-serif;
    font-size: {heading_size}px;
    color: {heading_color};
    margin-bottom: 12px;
}}
#{element_id} p {{
    font-family: '{body_font}', sans-serif;
    font-size: {body_size}px;
    color: {body_color};
    line-height: 1.5;
}}"""

        css_rules.append(rule_block)

    return "\n".join(css_rules)


def create_js_structure(events: list) -> list:
    items = []

    for item in events:
        element_id = item["id"]
        event_dict = item["data"]
        headline = event_dict.get("headline", "").strip()
        start_date = event_dict.get("start_date", "")
        end_date = event_dict.get("end_date", "")

        display_content = headline if headline else "Untitled Event"

        item_obj = {
            "id": element_id,
            "content": display_content,
            "start": start_date,
            "type": "box"
        }

        if end_date:
            item_obj["end"] = end_date
            item_obj["type"] = "range"

        items.append(item_obj)

    return items


# ==============================================================================
# EXPORT GENERATOR
# ==============================================================================

def build_website_content(timeline_data: list, output_dir: str) -> bool:
    if not output_dir:
        return False

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    os.makedirs(output_dir, exist_ok=True)
    
    imgs_dir = os.path.join(output_dir, "imgs")
    style_dir = os.path.join(output_dir, "style")

    os.makedirs(imgs_dir, exist_ok=True)
    os.makedirs(style_dir, exist_ok=True)

    index_path = os.path.join(output_dir, "index.html")
    css_path = os.path.join(style_dir, "style.css")
    css_timeline_path = os.path.join(style_dir, "timeline_stylesheet.css")
    js_path = os.path.join(output_dir, "script.js")

    events = parse_data(timeline_data, imgs_dir)

    html_items = create_html_structure(events)
    css_items = create_css_structure(events)
    items_list = create_js_structure(events)

    # 1. Generate index.html
    soup = BeautifulSoup(HTML_TEMPLATE, "html.parser")
    content_container = soup.find("main", class_="content")
    if content_container:
        prev_btn = content_container.find("button", id="prevBtn")
        next_btn = content_container.find("button", id="nextBtn")

        content_container.clear()

        if prev_btn:
            content_container.append(prev_btn)
        if next_btn:
            content_container.append(next_btn)

        fragment = BeautifulSoup(html_items, "html.parser")
        content_container.append(fragment)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    # 2. Copy timeline stylesheet & generate style.css
    shutil.copy("UI/Style/timeline_stylesheet.css", css_timeline_path)

    start_marker_css = "/* DYNAMIC STYLES START */"
    end_marker_css = "/* DYNAMIC STYLES END */"
    base_css = CSS_TEMPLATE.split(start_marker_css)[0]
    dynamic_css_block = f"\n\n{start_marker_css}\n{css_items}\n{end_marker_css}\n"

    with open(css_path, "w", encoding="utf-8") as f:
        f.write(base_css.strip() + dynamic_css_block)

    # 3. Generate script.js (Embedded Data Inline)
    full_js = f"var rawItems = {json.dumps(items_list, indent=2)};\n\n" + JS_TEMPLATE
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(full_js)

    return True