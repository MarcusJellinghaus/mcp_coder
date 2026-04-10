"""CSS styles for the iCoder TUI layout."""

CSS: str = """
OutputLog {
    height: 1fr;
    background: #1e1e1e;
    color: #d4d4d4;
}

InputArea {
    height: auto;
    background: #1e1e1e;
    color: #d4d4d4;
}

#streaming-tail {
    height: auto;
    background: #1e1e1e;
    color: #d4d4d4;
}

#input-hint {
    height: 1;
    background: #1e1e1e;
    color: #666666;
    text-align: right;
}

#input-hint.hidden {
    display: none;
}

CommandAutocomplete {
    display: none;
    height: auto;
    max-height: 8;
    background: #2d2d2d;
    color: #d4d4d4;
}

BusyIndicator {
    height: 1;
    background: #1e1e1e;
    color: #666666;
}
"""
