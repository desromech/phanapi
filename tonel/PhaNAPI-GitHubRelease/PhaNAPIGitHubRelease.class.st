Class {
	#name : #PhaNAPIGitHubRelease,
	#superclass : #PhaNAPIWebBinaryRepository,
	#instVars : [
		'platformMode',
		'currentPlatformMode'
	],
	#category : #'PhaNAPI-GitHubRelease'
}

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease class >> fetchLibrary: libraryName fromUser: userName repository: repository [
	^ self new fetchLibrary: libraryName fromUser: userName repository: repository
]

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease >> downloadAssetNamed: downloadFileName uri: downloadFileURI [
	| downloadTarget |
	downloadTarget := PhaNAPI uniqueInstance downloadsDirectory asFileReference / downloadFileName.
	downloadTarget parent ensureCreateDirectory.
	downloadTarget exists ifTrue: [ downloadTarget delete ].

	(self doHTTPRequest: [
		(ZnClient new
			"If we do not set the accept header, we might get a JSON describing the asset."
			accept: 'application/octet-stream';
			url: downloadFileURI;
			followRedirects: true;
			signalProgress: true;
			downloadTo: downloadTarget) 
	] withProgress: ('Downloading {1} ...' format: {downloadTarget basename})) ifFalse: [ 
		self error: 'Failed to download the requested library.'
	].

	^ downloadTarget
]

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease >> downloadUser: userName repository: repository latestVersionForMode: mode platform: platform [
	| latestVersionFiles downloadFile |
	latestVersionFiles := self getUser: userName repository: repository latestVersionForMode: mode platform: platform.
	latestVersionFiles ifEmpty: [ 
		self error: 'Failed to find library file.'
	].

	downloadFile := latestVersionFiles first.
	^ self downloadAssetNamed: downloadFile key uri: downloadFile value
]

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease >> extractFiles: fileList forMode: mode platform: platform [
	^ fileList select: [ :keyValue |
		| name |
		name := keyValue key.
		(name includesSubstring: mode) and: (name includesSubstring: platform , '_')
	]
]

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease >> fetchLibrary: libraryName fromUser: userName repository: repository [
	| archive |
	(PhaNAPI fullLibraryPathForCurrentPlatform: libraryName package: repository) ifNotNil: [
		^ self
	].

	archive := self downloadUser: userName repository: repository latestVersionForMode: currentPlatformMode platform: Smalltalk os phanapiPlatformName.
	PhaNAPI uniqueInstance decompressLibraryArchive: archive
]

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease >> getFileListFromVersion: releaseVersionInfo [
	^ (releaseVersionInfo at: 'assets') collect: [ :asset |
		(asset at: 'name') -> (asset at: 'url')
	]
]

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease >> getLatestVersionFileListForUser: userName repository: repository [
	^ self getFileListFromVersion: (self getLatestVersionForUser: userName repository: repository)
]

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease >> getLatestVersionForUser: userName repository: repository [
	| uri |
	uri := ('https://api.github.com/repos/:user/:repository/releases/latest'
		copyReplaceAll: ':user' with: userName)
		copyReplaceAll: ':repository' with: repository.
	^ self requestJSON: uri
]

{ #category : #'as yet unclassified' }
PhaNAPIGitHubRelease >> getUser: userName repository: repository latestVersionForMode: mode platform: platform [
	| fileList |
	fileList := self getLatestVersionFileListForUser: userName repository: repository.
	^ self extractFiles: fileList forMode: mode platform: platform
]

{ #category : #initialization }
PhaNAPIGitHubRelease >> initialize [
	super initialize.
	currentPlatformMode := 'release'
]
