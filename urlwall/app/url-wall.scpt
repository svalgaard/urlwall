--
-- AppleScript URL handler for URL-Wall
-- https://github.com/svalgaard/url-wall
--
-- https://developer.apple.com/library/archive/technotes/tn2065/
--

on open location theURL
	set AppPath to POSIX path of (path to me as text)
	set ScriptPath to AppPath & "/Contents/Resources/Assets/urlwall/cli.py"
	try
		do shell script "echo " & quoted form of theURL & " | python3 " & ScriptPath
	on error
		-- If Python fails, open directly in default browser
		do shell script "open " & quoted form of theURL
	end try
end open location
