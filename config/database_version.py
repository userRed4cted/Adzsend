# ==============================================
# DATABASE VERSION CONFIGURATION
# ==============================================
# This file tracks the database version for wipe notifications.
# When you reset the database, increment DATABASE_VERSION by 1.
# Users will see a notice that accounts have been wiped.
#
# HOW IT WORKS:
# - Users store the version number in their browser's localStorage
# - When they visit the site, if their stored version < DATABASE_VERSION,
#   they see a notice that the database was wiped
# - After dismissing, their stored version is updated
# ==============================================

# Increment this number each time you wipe/reset the database
DATABASE_VERSION = 1

# Message shown to users when database is wiped
DATABASE_WIPE_MESSAGE = "The database has been reset. All accounts have been wiped. Please sign up again to create a new account."
