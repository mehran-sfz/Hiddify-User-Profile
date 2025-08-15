from django.contrib.auth import get_user_model


def change_user_password_by_email(email, new_password):
    """
    this function changes the password of a user identified by their email.

    :param email: email of the user whose password is to be changed.
    :param new_password: new password to set for the user.
    :return: True if the password was changed successfully, False otherwise.
    """
    User = get_user_model()

    try:
        # get user by email
        user = User.objects.get(email=email)

        user.set_password(new_password) #hash new password
        # save the user instance to update the password in the database
        user.save()

        print(f"the password for user with email '{email}' has been changed successfully.")
        return True

    except User.DoesNotExist:
        print(f"no user found with email '{email}'.")
        return False
    except Exception as e:
        print(f"failed to change password for user with email '{email}': {e}")
        return False


def change_all_user_emails_to_lower_case():
    User = get_user_model()
    users = User.objects.all()
    for user in users:
        user.email = user.email.strip().lower()
        user.save()
    print("All user emails have been changed to lower case.")