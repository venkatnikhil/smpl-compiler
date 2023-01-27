class CustomSyntaxError(Exception):
    message_fmt = "Expected '{expected}' but found '{found}' at index: {at}"

    def __init__(self, **kwargs):
        self.message = kwargs.get("message")
        if not self.message:
            expected, found, idx = kwargs.get("expected"), kwargs.get("found"), kwargs.get("at")
            self.message = self.message_fmt.format(expected=expected, found=found, at=idx)

        super().__init__(self.message)

    def __repr__(self):
        return f"CustomSyntaxError: {self.message}"