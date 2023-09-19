import {
	AddAccount as AddAccountEvent,
	EditAccountName as EditAccountNameEvent,
} from "../generated/symmioMultiAccount/symmioMultiAccount";
import {Account, User} from "../generated/schema";
import {createNewAccount, createNewUser} from "./utils";

export function handleAddAccount(event: AddAccountEvent): void {
	let user = User.load(event.params.user.toHexString());
	if (user == null)
		user = createNewUser(event.params.user.toHexString(), event.address, event.block, event.transaction);
	createNewAccount(event.params.account.toHexString(), user, event.address, event.block, event.transaction, event.params.name)
}

export function handleEditAccountName(event: EditAccountNameEvent): void {
	let account = Account.load(event.params.account.toHexString())!;
	account.name = event.params.newName;
	account.updateTimestamp = event.block.timestamp;
	account.save();
}
