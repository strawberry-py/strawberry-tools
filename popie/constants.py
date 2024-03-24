# Supported languages. Default 'en' is implicit.
LANGUAGES = ("cs", "sk")

# Allowed context variable names.
# 'ctx' is discord.ext.commands.Context
# 'itx' is discord.Interactions which has different user variable
# 'utx' is TranslationContext with both guild and user information,
# 'gtx' is TranslationContext with only guild information
CONTEXTS = ("ctx", "itx", "utx", "gtx")
