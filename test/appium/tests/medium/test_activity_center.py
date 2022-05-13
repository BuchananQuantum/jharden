import pytest

from tests import marks
from tests.base_test_case import MultipleSharedDeviceTestCase, create_shared_drivers
from views.sign_in_view import SignInView


@pytest.mark.xdist_group(name="activity_center_medium_2")
@marks.medium
class TestActivityCenterMultipleDeviceMedium(MultipleSharedDeviceTestCase):

    @classmethod
    def setup_class(cls):
        cls.drivers, cls.loop = create_shared_drivers(2)
        cls.device_1, cls.device_2 = SignInView(cls.drivers[0]), SignInView(cls.drivers[1])
        cls.home_1, cls.home_2 = cls.device_1.create_user(), cls.device_2.create_user()
        cls.public_key_user_1, cls.username_1 = cls.home_1.get_public_key_and_username(return_username=True)
        cls.public_key_user_2, cls.username_2 = cls.home_2.get_public_key_and_username(return_username=True)
        [cls.group_chat_name_1, cls.group_chat_name_2, cls.group_chat_name_3, cls.group_chat_name_4, \
         cls.group_chat_name_5] = "GroupChat1", "GroupChat2", "GroupChat3", "GroupChat4", "GroupChat5"

        cls.message_from_sender = "Message sender"
        cls.home_2.home_button.double_click()
        cls.device_2_one_to_one_chat = cls.home_2.add_contact(cls.public_key_user_1)

    @marks.testrail_id(702183)
    def test_activity_center_reject_chats(self):
        self.device_2.just_fyi('Device2 sends a message in 1-1 chat to Device1')
        self.device_2_one_to_one_chat.send_message(self.message_from_sender)

        [home.home_button.double_click() for home in [self.home_1, self.home_2]]

        self.device_2.just_fyi('Device2 creates group chat with Device1')
        self.home_2.create_group_chat([self.username_1], group_chat_name=self.group_chat_name_1)
        self.home_2.home_button.double_click()
        self.home_1.home_button.double_click()

        self.device_1.just_fyi('Device1 rejects both chats and verifies they disappeared and not in Chats too')
        self.home_1.notifications_button.click()
        self.home_1.notifications_select_button.click()
        self.home_1.element_by_text_part(self.username_2[:10]).click()
        self.home_1.element_by_text_part(self.group_chat_name_1).click()
        self.home_1.notifications_reject_and_delete_button.click()
        if self.home_1.element_by_text_part(self.username_2[:20]).is_element_displayed(2):
            self.errors.append("1-1 chat is on Activity Center view after action made on it")
        if self.home_1.element_by_text_part(self.group_chat_name_1).is_element_displayed(2):
            self.errors.append("Group chat is on Activity Center view after action made on it")
            self.home_1.home_button.double_click()
        if self.home_1.element_by_text_part(self.username_2[:20]).is_element_displayed(2):
            self.errors.append("1-1 chat is added on home after rejection")
        if self.home_1.element_by_text_part(self.group_chat_name_1).is_element_displayed(2):
            self.errors.append("Group chat is added on home after rejection")

        self.home_1.just_fyi("Verify there are still no chats after relogin")
        self.home_1.relogin()
        if self.home_1.element_by_text_part(self.username_2[:20]).is_element_displayed(2):
            self.errors.append("1-1 chat appears on Chats view after relogin")
        if self.home_1.element_by_text_part(self.group_chat_name_1).is_element_displayed(2):
            self.errors.append("Group chat appears on Chats view after relogin")
        self.home_1.notifications_button.click()
        if self.home_1.element_by_text_part(self.username_2[:20]).is_element_displayed(2):
            self.errors.append("1-1 chat request reappears back in Activity Center view after relogin")
        if self.home_1.element_by_text_part(self.group_chat_name_1).is_element_displayed(2):
            self.errors.append("Group chat request reappears back in Activity Center view after relogin")

        self.errors.verify_no_errors()

    @marks.testrail_id(702184)
    def test_activity_center_accept_chats(self):
        [home.home_button.double_click() for home in [self.home_1, self.home_2]]

        self.device_2.just_fyi('Device2 creates 1-1 and Group chat again')
        self.home_2.get_chat_from_home_view(self.username_1).click()
        self.device_2_one_to_one_chat.send_message(self.message_from_sender)
        self.device_2_one_to_one_chat.home_button.double_click()
        self.home_2.create_group_chat([self.username_1], group_chat_name=self.group_chat_name_2)

        self.device_1.just_fyi('Device1 accepts both chats (via Select All button) and verifies they disappeared '
                               'from activity center view but present on Chats view')
        self.home_1.notifications_button.click()
        self.home_1.notifications_select_button.click()

        self.home_1.notifications_select_all.click()
        self.home_1.notifications_accept_and_add_button.click()
        if self.home_1.element_by_text_part(self.username_2[:20]).is_element_displayed(2):
            self.errors.append("1-1 chat request stays on Activity Center view after it was accepted")
        if self.home_1.element_by_text_part(self.group_chat_name_2).is_element_displayed(2):
            self.errors.append("Group chat request stays on Activity Center view after it was accepted")
        self.home_1.home_button.double_click()
        if not self.home_1.element_by_text_part(self.username_2[:20]).is_element_displayed(2):
            self.errors.append("1-1 chat is not added on home after accepted from Activity Center")
        if not self.home_1.element_by_text_part(self.group_chat_name_2).is_element_displayed(2):
            self.errors.append("Group chat is not added on home after accepted from Activity Center")

        self.errors.verify_no_errors()

    @marks.testrail_id(702185)
    def test_activity_center_notifications_on_mentions_in_groups_and_empty_state(self):
        [home.home_button.double_click() for home in [self.home_1, self.home_2]]

        self.home_1.just_fyi("Joining Group chat, receiving community link in there")
        device_1_one_to_one_chat = self.home_1.add_contact(self.public_key_user_2)
        device_1_one_to_one_chat.home_button.double_click()

        pub_1 = self.home_1.create_group_chat(user_names_to_add=[self.username_2], group_chat_name=self.group_chat_name_3)
        pub_2 = self.home_2.get_chat(self.group_chat_name_3).click()

        pub_1.get_back_to_home_view()

        self.home_2.get_chat_from_home_view(self.group_chat_name_3).click()
        pub_2.select_mention_from_suggestion_list(self.username_1, self.username_1[:2])
        pub_2.send_as_keyevent("group")
        group_chat_message = self.username_1 + " group"
        pub_2.send_message_button.click()

        if not self.home_1.notifications_unread_badge.is_element_displayed():
            self.errors.append("Unread badge is NOT shown after receiving mentions from Group")
        self.home_1.notifications_unread_badge.wait_and_click(30)

        self.home_1.just_fyi("Check that notification from group is presented in Activity Center")
        if self.home_1.get_chat_from_activity_center_view(self.username_2).chat_message_preview == group_chat_message:
            self.home_1.just_fyi("Open group chat where user mentioned and return to Activity Center")
            self.home_1.get_chat_from_activity_center_view(self.username_2).click()
            self.home_1.home_button.double_click()
            self.home_1.notifications_button.click()
        else:
            self.errors.append("No mention in Activity Center for Group Chat")

        self.home_1.just_fyi("Check there are no unread messages counters on chats after message read")
        if self.home_1.get_chat_from_home_view(self.group_chat_name_3).new_messages_counter.text == "1":
            self.errors.append("Unread message indicator is kept after all messages read in chats")

        self.home_1.just_fyi("Check there is an empty view on Activity Center")
        self.home_1.notifications_button.click()
        if not self.home_1.element_by_translation_id('empty-activity-center').is_element_present():
            self.errors.append("It appears Activity Center still has some chats after user opened all of them")

        self.device_1.just_fyi('Device1 removes Device2 from contacts (for the next test)')
        self.home_1.home_button.double_click()
        self.home_1.get_chat_from_home_view(self.username_2).click()
        self.device_1_one_to_one_chat = self.home_1.get_chat_view()
        self.device_1_one_to_one_chat.chat_options.click()
        self.device_1_one_to_one_chat.view_profile_button.click()
        self.device_1_one_to_one_chat.remove_from_contacts.click_until_absense_of_element(
            self.device_1_one_to_one_chat.remove_from_contacts)
        self.device_1_one_to_one_chat.close_button.click()

        self.device_1.just_fyi('Device1 removes 1-1 chat from home screen (for the next test)')
        self.home_1.home_button.double_click()
        self.home_1.delete_chat_long_press(self.username_2)

        self.errors.verify_no_errors()

    @marks.testrail_id(702187)
    def test_activity_center_accept_chats_only_from_contacts(self):
        [home.home_button.double_click() for home in [self.home_1, self.home_2]]

        self.device_1.just_fyi('Device1 sets permissions to accept chat requests only from trusted contacts')
        profile_1 = self.home_1.profile_button.click()
        profile_1.privacy_and_security_button.click()
        profile_1.accept_new_chats_from.click()
        profile_1.accept_new_chats_from_contacts_only.click()
        profile_1.profile_button.click()

        self.device_1.just_fyi('Device2 creates 1-1 chat Group chats')
        self.home_2.home_button.double_click()
        self.home_2.get_chat(self.username_1).click()
        self.device_2_one_to_one_chat.send_message(self.message_from_sender)
        self.device_2_one_to_one_chat.home_button.double_click()
        self.home_2.create_group_chat([self.username_1], group_chat_name=self.group_chat_name_4)

        self.device_1.just_fyi('Device1 check there are no any chats in Activity Center nor Chats view')
        self.home_1.home_button.double_click()
        if self.home_1.element_by_text_part(self.username_2).is_element_displayed() or self.home_1.element_by_text_part(
                self.group_chat_name_4).is_element_displayed():
            self.errors.append("Chats are present on Chats view despite they created by non-contact")
        self.home_1.notifications_button.click()
        if self.home_1.element_by_text_part(self.username_2).is_element_displayed() or self.home_1.element_by_text_part(
                self.group_chat_name_4).is_element_displayed():
            self.errors.append("Chats are present in Activity Center view despite they created by non-contact")

        self.device_1.just_fyi('Device1 adds Device2 in Contacts so chat requests should be visible now')
        self.home_1.home_button.double_click()
        self.home_1.add_contact(self.public_key_user_2)

        self.device_1.just_fyi('Device2 creates 1-1 chat Group chats once again')
        self.home_2.home_button.double_click()
        self.home_2.get_chat_from_home_view(self.username_1).click()
        self.device_2_one_to_one_chat.send_message(self.message_from_sender)
        self.device_2_one_to_one_chat.home_button.double_click()
        self.home_2.create_group_chat([self.username_1], group_chat_name=self.group_chat_name_5)

        self.device_1.just_fyi('Device1 verifies 1-1 chat Group chats are visible')
        self.home_1.home_button.double_click()
        if not self.home_1.element_by_text_part(
                self.username_2).is_element_displayed() or not self.home_1.element_by_text_part(
            self.group_chat_name_5).is_element_displayed():
            self.errors.append("Chats are not present on Chats view while they have to!")

        self.errors.verify_no_errors()