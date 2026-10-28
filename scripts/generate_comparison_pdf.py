"""Generate a professional, multi-page executive PDF comparing
the Agentic Travel Planner prototype against a vanilla LLM (Gemini/ChatGPT).
"""

from __future__ import annotations

import os
from typing import List, Tuple


class PDFBuilder:
    def __init__(self, filename: str, page_w: float = 612.0, page_h: float = 792.0):
        self.filename = filename
        self.page_w = page_w
        self.page_h = page_h
        self.pages: List[bytearray] = []
        self.current_stream: bytearray = bytearray()
        self.margin_x = 45.0
        self.margin_y = 45.0
        self.y = page_h - self.margin_y

    def new_page(self):
        if self.current_stream:
            self.pages.append(self.current_stream)
        self.current_stream = bytearray()
        self.y = self.page_h - self.margin_y - 24.0
        self._draw_page_header_footer()

    def _draw_page_header_footer(self):
        # Top banner line
        self.draw_rect(self.margin_x, self.page_h - 30, self.page_w - 2 * self.margin_x, 1.5, fill_color=(0.15, 0.39, 0.92))
        # Top small header
        self.draw_text("AGENTIC TRAVEL PLANNER - TECHNICAL ARCHITECTURE & PRD COMPARISON", self.margin_x, self.page_h - 24, font="/F2", size=7.5, color=(0.4, 0.45, 0.55))
        # Bottom small footer
        self.draw_rect(self.margin_x, 34, self.page_w - 2 * self.margin_x, 0.75, fill_color=(0.88, 0.91, 0.94))
        self.draw_text("Confidential & Proprietary - Agentic Travel Planner v1.0", self.margin_x, 22, font="/F1", size=8, color=(0.5, 0.55, 0.65))

    def check_space(self, needed_h: float):
        if self.y - needed_h < self.margin_y + 15:
            self.new_page()

    def draw_rect(self, x: float, y: float, w: float, h: float, fill_color=None, stroke_color=None, stroke_width=1.0):
        cmd = []
        if stroke_color:
            cmd.append(f"{stroke_width} w {stroke_color[0]} {stroke_color[1]} {stroke_color[2]} RG")
        if fill_color:
            cmd.append(f"{fill_color[0]} {fill_color[1]} {fill_color[2]} rg")
        op = "B" if (fill_color and stroke_color) else ("f" if fill_color else "s")
        cmd.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}")
        self.current_stream.extend((" ".join(cmd) + "\n").encode("latin1"))

    def draw_text(self, text: str, x: float, y: float, font="/F1", size=10.0, color=(0.1, 0.1, 0.1)):
        clean = (
            text.replace("INR ₹", "INR")
            .replace("₹", "INR ")
            .replace("•", "-")
            .replace("■", "*")
            .replace("—", "--")
            .replace("“", '"')
            .replace("”", '"')
            .replace("‘", "'")
            .replace("’", "'")
            .replace("≤", "<=")
            .replace("≥", ">=")
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
        # Ensure ascii compatibility
        clean = clean.encode("ascii", "ignore").decode("latin1")
        r, g, b = color
        stream_cmd = (
            f"BT {r:.3f} {g:.3f} {b:.3f} rg {font} {size:.2f} Tf "
            f"{x:.2f} {y:.2f} Td ({clean}) Tj ET\n"
        )
        self.current_stream.extend(stream_cmd.encode("latin1"))

    def add_title_block(self, title: str, subtitle: str, meta: str):
        self.check_space(110)
        # Background card
        card_h = 95.0
        card_y = self.y - card_h
        self.draw_rect(self.margin_x, card_y, self.page_w - 2 * self.margin_x, card_h, fill_color=(0.96, 0.98, 1.0), stroke_color=(0.8, 0.88, 1.0), stroke_width=1.0)
        # Left brand bar
        self.draw_rect(self.margin_x, card_y, 4.0, card_h, fill_color=(0.15, 0.39, 0.92))
        
        self.draw_text("SYSTEM ARCHITECTURE BRIEFING", self.margin_x + 16, card_y + card_h - 22, font="/F2", size=8.5, color=(0.15, 0.39, 0.92))
        self.draw_text(title, self.margin_x + 16, card_y + card_h - 44, font="/F2", size=17.0, color=(0.06, 0.1, 0.2))
        self.draw_text(subtitle, self.margin_x + 16, card_y + card_h - 62, font="/F3", size=10.0, color=(0.25, 0.32, 0.45))
        self.draw_text(meta, self.margin_x + 16, card_y + card_h - 82, font="/F1", size=8.0, color=(0.45, 0.5, 0.6))
        self.y = card_y - 20

    def add_section_header(self, title: str, icon: str = "■"):
        self.check_space(38)
        self.draw_rect(self.margin_x, self.y - 4, self.page_w - 2 * self.margin_x, 24, fill_color=(0.94, 0.96, 0.99))
        self.draw_rect(self.margin_x, self.y - 4, 3.0, 24, fill_color=(0.15, 0.39, 0.92))
        self.draw_text(f"{icon}  {title.upper()}", self.margin_x + 10, self.y + 4, font="/F2", size=11.0, color=(0.1, 0.18, 0.35))
        self.y -= 34

    def add_paragraph(self, text: str, font="/F1", size=9.5, color=(0.2, 0.24, 0.3), line_height=14.0):
        # Simple word wrap at ~95 chars
        words = text.split()
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 92:
                lines.append(" ".join(cur[:-1]))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))

        for line in lines:
            self.check_space(line_height)
            self.draw_text(line, self.margin_x, self.y, font=font, size=size, color=color)
            self.y -= line_height
        self.y -= 6

    def add_callout(self, title: str, text: str, color_theme="blue"):
        lines = text.split("\n")
        h = 32 + len(lines) * 14
        self.check_space(h)
        bg = (0.95, 0.98, 1.0) if color_theme == "blue" else (0.95, 1.0, 0.96)
        stroke = (0.7, 0.85, 1.0) if color_theme == "blue" else (0.7, 0.9, 0.75)
        bar = (0.15, 0.39, 0.92) if color_theme == "blue" else (0.05, 0.6, 0.4)
        
        box_y = self.y - h
        self.draw_rect(self.margin_x, box_y, self.page_w - 2 * self.margin_x, h, fill_color=bg, stroke_color=stroke, stroke_width=1.0)
        self.draw_rect(self.margin_x, box_y, 4.0, h, fill_color=bar)
        self.draw_text(title, self.margin_x + 14, box_y + h - 18, font="/F2", size=10.0, color=(0.1, 0.2, 0.4))
        
        cy = box_y + h - 34
        for l in lines:
            self.draw_text(l, self.margin_x + 14, cy, font="/F1", size=8.8, color=(0.2, 0.25, 0.35))
            cy -= 14
        self.y = box_y - 14

    def add_table(self, headers: List[str], rows: List[List[str]], col_widths: List[float]):
        total_w = sum(col_widths)
        hdr_h = 24.0
        self.check_space(hdr_h + 20)
        
        # Header Row
        self.draw_rect(self.margin_x, self.y - hdr_h, total_w, hdr_h, fill_color=(0.12, 0.18, 0.32))
        cx = self.margin_x
        for i, h in enumerate(headers):
            self.draw_text(h, cx + 8, self.y - 16, font="/F2", size=8.5, color=(1.0, 1.0, 1.0))
            cx += col_widths[i]
        self.y -= hdr_h

        # Data Rows
        for r_idx, row in enumerate(rows):
            # Calculate height needed for wrapped lines
            max_lines = 1
            wrapped_cells = []
            for i, cell in enumerate(row):
                chars_per_line = int(col_widths[i] / 5.2)
                words = cell.split()
                lines = []
                cur = []
                for w in words:
                    cur.append(w)
                    if len(" ".join(cur)) > chars_per_line:
                        lines.append(" ".join(cur[:-1]))
                        cur = [w]
                if cur:
                    lines.append(" ".join(cur))
                wrapped_cells.append(lines)
                if len(lines) > max_lines:
                    max_lines = len(lines)

            row_h = max(22.0, max_lines * 12.0 + 8.0)
            self.check_space(row_h)

            bg_color = (0.97, 0.98, 1.0) if r_idx % 2 == 1 else (1.0, 1.0, 1.0)
            self.draw_rect(self.margin_x, self.y - row_h, total_w, row_h, fill_color=bg_color, stroke_color=(0.88, 0.91, 0.94), stroke_width=0.5)

            cx = self.margin_x
            for i, lines in enumerate(wrapped_cells):
                cell_y = self.y - 14.0
                for line in lines:
                    font = "/F2" if i == 0 else "/F1"
                    color = (0.05, 0.15, 0.35) if (i == 2) else ((0.1, 0.1, 0.1) if i == 0 else (0.4, 0.2, 0.2))
                    self.draw_text(line, cx + 8, cell_y, font=font, size=8.0, color=color)
                    cell_y -= 11.0
                cx += col_widths[i]

            self.y -= row_h
        self.y -= 14

    def build(self) -> bytes:
        if self.current_stream:
            self.pages.append(self.current_stream)

        pdf = bytearray()
        pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []

        def add_obj(data: bytes):
            offsets.append(len(pdf))
            pdf.extend(f"{len(offsets)} 0 obj\n".encode("latin1"))
            pdf.extend(data)
            pdf.extend(b"\nendobj\n")

        total_pages = len(self.pages)
        page_obj_ids = [3 + i * 2 for i in range(total_pages)]

        # 1 0 obj: Catalog
        add_obj(b"<< /Type /Catalog /Pages 2 0 R >>")

        # 2 0 obj: Pages
        kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
        add_obj(f"<< /Type /Pages /Kids [{kids_str}] /Count {total_pages} >>".encode("latin1"))

        # Base font references: F1=Helvetica, F2=Helvetica-Bold, F3=Helvetica-Oblique
        font_res_ids = {
            "F1": 2 + total_pages * 2 + 1,
            "F2": 2 + total_pages * 2 + 2,
            "F3": 2 + total_pages * 2 + 3,
        }

        # Page objects & Content streams
        for i, page_stream in enumerate(self.pages):
            content_id = page_obj_ids[i] + 1
            # Add page number to stream
            footer_text = f"Page {i + 1} of {total_pages}".encode("latin1")
            page_stream.extend(
                f"BT 0.5 0.55 0.65 rg /F1 8.0 Tf {self.page_w - self.margin_x - 55:.2f} 22.0 Td ({footer_text.decode('latin1')}) Tj ET\n".encode("latin1")
            )

            # Page Object
            add_obj(
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.page_w} {self.page_h}] "
                f"/Resources << /Font << /F1 {font_res_ids['F1']} 0 R /F2 {font_res_ids['F2']} 0 R /F3 {font_res_ids['F3']} 0 R >> >> "
                f"/Contents {content_id} 0 R >>".encode("latin1")
            )
            # Content Stream Object
            add_obj(f"<< /Length {len(page_stream)} >>\nstream\n".encode("latin1") + page_stream + b"\nendstream")

        # Font Objects
        add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
        add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>")

        # Xref table
        xref_pos = len(pdf)
        pdf.extend(f"xref\n0 {len(offsets) + 1}\n0000000000 65535 f \n".encode("latin1"))
        for off in offsets:
            pdf.extend(f"{off:010d} 00000 n \n".encode("latin1"))
        pdf.extend(f"trailer\n<< /Size {len(offsets) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin1"))

        with open(self.filename, "wb") as f:
            f.write(pdf)

        return bytes(pdf)


def generate_document():
    pdf = PDFBuilder(
        filename="/Users/anshchikara/Desktop/Agentic-Travel-Planner/Agentic_Travel_Planner_vs_Simple_LLM.pdf"
    )
    pdf.new_page()

    # Title Block
    pdf.add_title_block(
        title="Agentic Travel Planner vs. Simple LLM Model",
        subtitle="A Technical & Architectural Whitepaper on Grounded Multi-Agent Systems",
        meta="Product Requirements Document (PRD v1.0) • India-First Localization • Production Architecture",
    )

    # Executive Summary
    pdf.add_section_header("1. Executive Summary")
    pdf.add_paragraph(
        "A critical question in generative AI is: 'Why build an agentic travel system when a user can simply open "
        "Gemini or ChatGPT and ask for a trip plan?'"
    )
    pdf.add_paragraph(
        "The short answer is: A standard LLM predicts what a travel plan sounds like; an Agentic Travel Planner "
        "actually executes the planning work. A vanilla LLM has no live inventory, hallucinates flight numbers, "
        "invents out-of-date prices, makes simple mathematical errors in group splits, cannot check opening hours "
        "or transit buffers, and cannot connect to booking or payment providers."
    )
    pdf.add_callout(
        "The Core Principle (from PRD v1.0 Section 20)",
        "\"The product's defining principle: The AI should not merely tell users how to plan a trip.\n"
        "It should perform the planning work, validate its results, and help execute the plan--with\n"
        "transparency, mathematical certainty, and user authorization.\"",
        color_theme="blue"
    )
    pdf.add_paragraph(
        "Travel planning is a high-stakes domain involving non-refundable payments, immovable flight schedules, "
        "and physical transit constraints. When an AI hallucinates a flight time or calculates a budget incorrectly, "
        "the user suffers real financial loss or missed connections. Solving this requires transitioning from "
        "a zero-shot text generator to an autonomous multi-agent orchestration architecture."
    )

    # Page 2: Comparison Table
    pdf.new_page()
    pdf.add_section_header("2. Comprehensive Capability Comparison")
    headers = ["Capability", "Simple LLM (Gemini/ChatGPT)", "Agentic Travel Planner (Our Prototype)"]
    rows = [
        [
            "Flight & Hotel Data",
            "Hallucinates routes, non-existent flights, and fabricated prices based on historical training data.",
            "Queries live Amadeus API, Indian carrier hubs (IndiGo, Air India, Vistara), and live Hotellook/Booking engines."
        ],
        [
            "Budget & Arithmetic",
            "Token-prediction math. Tables often have row sums that contradict the total; misses group splits.",
            "Deterministic Python engine (travel_agent/tools/budget.py). 100% exact math, per-traveler split, and overrun alerts."
        ],
        [
            "Verification & Audit",
            "Cannot differentiate between a real price and a hallucinated guess.",
            "Audits every line item as 'Verified' (live API) vs 'Estimate' (benchmarked index), calculating verified ratio %."
        ],
        [
            "Action & Booking",
            "Pure text advice. The user must manually open 10 tabs and search dates from scratch.",
            "Generates executable affiliate deep links (Aviasales, RentalCars) and Stripe Checkout sessions directly."
        ],
        [
            "Feasibility & Limits",
            "Suggests impossible itineraries (e.g. 5 distant attractions in 4 hours, ignoring traffic).",
            "Deterministic validator checks daily active hours (relaxed 6h, moderate 8.5h) and enforces transit buffers."
        ],
        [
            "State & Persistence",
            "Ephemeral chat log. Once the tab is closed, all structured trip data is lost.",
            "SQLite database layer (travel_planner.db) storing TripRecord, DayPlan, and ActivityItem for repeat editing."
        ],
        [
            "User Interface",
            "Single infinite text scroll. Difficult to inspect budget line items or isolated days.",
            "Dual-pane Trip Workspace with dedicated tabs: Travel Assistant, Itinerary, Budget Intelligence, Saved Trips."
        ],
        [
            "India Localization",
            "Defaults to US context ($ USD, foreign departure airports) unless repeatedly prompted.",
            "Auto-detects location & timezone. Defaults to INR (Rs.), major domestic hubs (DEL/BOM/BLR), and Indian airlines."
        ]
    ]
    pdf.add_table(headers, rows, [100.0, 195.0, 227.0])

    # Page 3: Deep Dive into Architectural Pillars
    pdf.new_page()
    pdf.add_section_header("3. The Five Architectural Pillars")

    pdf.add_paragraph(
        "To achieve production-grade reliability, our prototype implements five specialized architectural layers "
        "specified in PRD v1.0:"
    )

    pdf.add_callout(
        "Pillar 1: Deterministic Budget Intelligence Engine (PRD Section 7)",
        "Section 7 mandates: 'The budget engine must be a deterministic calculation service, not solely an LLM-generated estimate.'\n"
        "- Implemented in travel_agent/tools/budget.py.\n"
        "- Performs IEEE-754 arithmetic across 7 standard categories (transport, stays, food, local transit, activities, permits, contingency).\n"
        "- Computes total expenses and per-person cost for N travelers.\n"
        "- Compares against target budgets, flags overages, and generates targeted savings tips in INR.\n"
        "- Labels each item as Verified vs Estimate, computing a rigorous audit ratio.",
        color_theme="blue"
    )

    pdf.add_callout(
        "Pillar 2: Tool Grounding & Authorization Gates (PRD Section 5 & 11)",
        "Standard LLMs generate text. Our Agent Orchestrator executes a stateful tool loop:\n"
        "• Live flight searches (Amadeus + Indian IATA carrier registry: 6E, AI, UK, QP, SG, IX).\n"
        "• Live weather forecasts (Open-Meteo current and archive climate proxies).\n"
        "• Direct booking execution via pre-filled partner deeplinks.\n"
        "• Stripe Checkout session generation (create_payment_session) with default INR support.\n"
        "• Human-in-the-loop authorization gates: no charge or transaction occurs without explicit user confirmation.",
        color_theme="green"
    )

    pdf.add_callout(
        "Pillar 3: Programmatic Constraint & Feasibility Enforcement (PRD Section 13.2)",
        "Standard LLMs lack spatial and temporal reasoning. Our feasibility engine (travel_agent/tools/feasibility.py):\n"
        "• Evaluates daily schedules against travel pace (Relaxed <= 6.0h/day, Moderate <= 8.5h/day, Intense <= 11.0h/day).\n"
        "• Enforces mandatory 35-minute transit buffers between distinct sightseeing stops.\n"
        "• Flags overload warnings if a single day exceeds 4 separate stops.\n"
        "• Computes an objective Feasibility Score (0 to 100) and returns actionable adjustment recommendations.",
        color_theme="blue"
    )

    # Page 3: Persistence, UX, and India Localization
    pdf.new_page()
    pdf.add_section_header("4. Data Persistence & Dual-Pane Workspace UX")

    pdf.add_paragraph(
        "A travel plan is a multi-day living document, not a one-off conversational answer. "
        "Our system separates conversational planning from structured trip artifacts:"
    )

    pdf.add_callout(
        "Pillar 4: Structured Data Model & SQLite Persistence (PRD Section 12)",
        "• Implemented in travel_agent/storage/models.py and travel_agent/storage/db.py.\n"
        "• Formal entities: TripRecord, DayPlan, ActivityItem, and BudgetBreakdown.\n"
        "• Stored in durable local SQLite (travel_planner.db), ready for PostgreSQL migration.\n"
        "• REST Endpoints: GET /api/trips, GET /api/trips/{id}, POST /api/trips, DELETE /api/trips/{id}.\n"
        "• Allows users to reload saved itineraries back into the chat session for iterative refinement (FR-06 & FR-10).",
        color_theme="green"
    )

    pdf.add_callout(
        "Pillar 5: Trip Workspace Dual-Pane Interface (PRD Section 8.3 & 8.4)",
        "The web application (static/index.html & static/js/app.js) provides a dedicated multi-tab workspace:\n"
        "1. Travel Assistant: Real-time chat with streaming thought signatures and an Agent Activity Bar with cancel support.\n"
        "2. Itinerary & Timeline: Day-by-day interactive timeline with activity duration tags and one-click 'Save Trip'.\n"
        "3. Budget Intelligence: Live itemized breakdown table, per-traveler split, verified status tags, and progress bar.\n"
        "4. Flights & Stays: Live airline and hotel deals with direct partner booking buttons.\n"
        "5. Saved Trips: Gallery of stored itineraries with quick restore and delete actions.",
        color_theme="blue"
    )

    pdf.add_section_header("5. India-First Localization Architecture")
    pdf.add_paragraph(
        "The system incorporates comprehensive Indian travel defaults: "
        "Automatic location & timezone detection, currency in Indian Rupee (INR), native support for 35+ Indian airports "
        "(DEL, BOM, BLR, HYD, MAA, CCU, GOI, COK, SXR, JAI), domestic carriers (IndiGo, Air India, Vistara, Akasa), "
        "and domestic holiday benchmarks (Goa, Kerala, Himachal, Kashmir, Rajasthan) as well as outbound Indian hubs (Dubai, Thailand, Bali)."
    )

    pdf.add_section_header("6. Conclusion & Strategic Value")
    pdf.add_paragraph(
        "While a standard LLM acts as an encyclopedic conversationalist, the Agentic Travel Planner operates as an "
        "integrated travel operating system. By combining LLM reasoning with deterministic microservices, live API retrieval, "
        "persistent relational storage, and an interactive workspace, it transforms vague travel desires into actionable, "
        "mathematically sound, and bookable itineraries."
    )

    pdf.build()
    print("PDF build complete: /Users/anshchikara/Desktop/Agentic-Travel-Planner/Agentic_Travel_Planner_vs_Simple_LLM.pdf")


if __name__ == "__main__":
    generate_document()
