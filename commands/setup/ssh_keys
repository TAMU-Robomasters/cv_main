#!/usr/bin/env -S deno run --allow-all
const { run, Timeout, Env, Cwd, Stdin, Stdout, Stderr, Out, Overwrite, AppendTo, zipInto, mergeInto, returnAsString, } = await import(`https://deno.land/x/sprinter@0.3.1/index.js`)
const { FileSystem, Console } = await import(`https://deno.land/x/file_system_js@0.0.22/main/deno.js`)
const { vibrance } = (await import('https://cdn.skypack.dev/vibrance@v0.1.33')).default

const sshFolder = `${FileSystem.home}/.ssh/`
const authorizedKeysPath = `${FileSystem.home}/.ssh/authorized_keys`
const defaultPrivateKeyPath = `${sshFolder}/id_rsa`
const defaultPublicKeyPath = `${sshFolder}/id_rsa.pub`

// 
// 
// main 
// 
// 
await verifyAndSetupSshFolderStructure()
console.log(`

    __________________      __________________
    | "Your" Machine |  ->  | Remote Machine | 
    ------------------      ------------------  

`)
if (await Console.askFor.yesNo("Is this script running on your machine right now?")) {
    await ensurePrivatePublicRsaKeyExists()
    console.log("Now run this same script on the remote server (on your account)")
    console.log("Paste the value below when it asks for your public key")
    console.log("(and FYI you can show this to anyone, its not private)")
    console.log()
    vibrance.bgBlack.blue(await FileSystem.read(defaultPublicKeyPath)).log()
    console.log()
    console.log()
} else {
    let publicKeyString = ""
    while (publicKeyString.length == 0) {
        publicKeyString = await Console.askFor.line(`Whats the public key of your machine?\n(run this script on your machine to get it)`)
    }
    await FileSystem.append({
        path: authorizedKeysPath,
        data: publicKeyString+"\n",
    })
    // TODO: assumes debian/ubuntu
    if (await Console.askFor.yesNo(`Would you like to restart ssh to make the change take effect?`)) {
        await run("sudo", "systemctl", "restart", "ssh.service")
    }
}

function escapeShellArgument(string) {
    return `'${string.replace(/'/,`'"'"'`)}'`
}

async function ensurePrivatePublicRsaKeyExists() {
    let privateKey = await FileSystem.info(defaultPrivateKeyPath)
    let publicKey = await FileSystem.info(defaultPublicKeyPath)
    while (!privateKey.isFile || !publicKey.isFile) {
        console.log("\nLooks like your private key doesn't exist so lets make one")
        vibrance.bgBlack.white("    running: ").bgBlack.blue("ssh-keygen -t rsa").log()
        await run("ssh-keygen", "-t", "rsa", "-f", defaultPrivateKeyPath)
        privateKey = await FileSystem.info(defaultPrivateKeyPath)
        publicKey = await FileSystem.info(defaultPublicKeyPath)
    }
}

async function getFingerprint(path=defaultPublicKeyPath) {
    return run("ssh-keygen", "-lf", path, Stdout(returnAsString))
}

async function verifyAndSetupSshFolderStructure() {
    await FileSystem.ensureIsFolder(sshFolder)
    const authInfo = await FileSystem.info(authorizedKeysPath)
    if (!authInfo.exists) {
        await Deno.writeTextFile(authorizedKeysPath, "")
    }
    // following: https://superuser.com/a/925859/399438

    // SSH folder on the server needs 700 permissions: chmod 700 /home/$USER/.ssh
    await FileSystem.addPermissions({
        path: sshFolder,
        permissions: {
            owner:{
                canRead: true,
                canWrite: true,
                canExecute: true,
            }, 
            group:{
                canRead: false,
                canWrite: false,
                canExecute: false,
            },
            others:{
                canRead: false,
                canWrite: false,
                canExecute: false,

            }
        },
    })
    // authorized_keys file needs 644 permissions: chmod 644 /home/$USER/.ssh/authorized_keys
    await FileSystem.addPermissions({
        path: authorizedKeysPath,
        permissions: {
            owner:{
                canRead: true,
                canWrite: true,
                canExecute: false,
            }, 
            group:{
                canRead: true,
                canWrite: false,
                canExecute: false,
            },
            others:{
                canRead: true,
                canWrite: false,
                canExecute: false,

            }
        },
    })
    // Make sure that user owns the files/folders and not root: chown user:user authorized_keys and chown user:user /home/$USER/.ssh
    const username = await run("whoami", Stdout(returnAsString))
    const fileOwner = await run("stat", "-c", "%U", sshFolder, Stdout(returnAsString))
    if (username != fileOwner) {
        console.log(`\nFor some reason you're not the owner of your own home/.ssh/ folder (strange)`)
        console.log(`    your  username: ${username}`)
        console.log(`    owner username: ${fileOwner}`)
        console.log(`Lets change that:\n`)
        await run("sudo", "chown", username, sshFolder)
    }
}