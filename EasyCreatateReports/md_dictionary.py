# Λεξικό αντιστοιχίας Markdown κανόνων σε HTML tags
MARKDOWN_RULES = {
    # Inline formatting (Μορφοποίηση εντός κειμένου)
    'bold': {
        'pattern': r'\*\*(.+?)\*\*',
        'replacement': r'<strong>\1</strong>'
    },
    'italic': {
        'pattern': r'\*(.+?)\*',
        'replacement': r'<em>\1</em>'
    },
    'horizontal_rule': {
        'pattern': r'^---+$',
        'replacement': '<hr>'
    }
}
