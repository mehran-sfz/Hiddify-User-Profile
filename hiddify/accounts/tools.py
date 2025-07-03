from django.contrib.auth import get_user_model

def change_user_password_by_phone(phone_number, new_password):
    """
    this function changes the password of a user identified by their phone number.

    :param phone_number: phone number of the user whose password is to be changed.
    :param new_password: new password to set for the user.
    :return: True if the password was changed successfully, False otherwise.
    """
    User = get_user_model()

    try:
        # get user by phone number
        user = User.objects.get(phone_number=phone_number)

        user.set_password(new_password) #hash new password
        # save the user instance to update the password in the database
        user.save()

        print(f"the password for user with phone number '{phone_number}' has been changed successfully.")
        return True

    except User.DoesNotExist:
        print(f"no user found with phone number '{phone_number}'.")
        return False
    except Exception as e:
        print(f"failed to change password for user with phone number '{phone_number}': {e}")
        return False
    
