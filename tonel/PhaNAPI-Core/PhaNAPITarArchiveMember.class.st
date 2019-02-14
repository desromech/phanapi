Class {
	#name : #PhaNAPITarArchiveMember,
	#superclass : #ArchiveMember,
	#instVars : [
		'fileMode',
		'ownerUserID',
		'groupID',
		'lastModificationTime',
		'typeFlag',
		'linkedFileName',
		'ownerUserName',
		'ownerGroupName',
		'deviceMajorNumber',
		'deviceMinorNumber',
		'fileSize',
		'content'
	],
	#category : #'PhaNAPI-Core-Tar'
}

{ #category : #accessing }
PhaNAPITarArchiveMember >> deviceMajorNumber [
	^ deviceMajorNumber
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> deviceMajorNumber: anObject [
	deviceMajorNumber := anObject
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> deviceMinorNumber [
	^ deviceMinorNumber
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> deviceMinorNumber: anObject [
	deviceMinorNumber := anObject
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> fileMode [
	^ fileMode
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> fileMode: anObject [
	fileMode := anObject
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> fileSize [
	^ fileSize
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> fileSize: anObject [
	fileSize := anObject
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> groupID [
	^ groupID
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> groupID: anObject [
	groupID := anObject
]

{ #category : #testing }
PhaNAPITarArchiveMember >> isBlockSpecial [
	^ typeFlag = $4
]

{ #category : #testing }
PhaNAPITarArchiveMember >> isCharacterSpecial [
	^ typeFlag = $3
]

{ #category : #testing }
PhaNAPITarArchiveMember >> isContinousFile [
	^ typeFlag = $7
]

{ #category : #testing }
PhaNAPITarArchiveMember >> isDirectory [
	^ typeFlag = $5
]

{ #category : #testing }
PhaNAPITarArchiveMember >> isFIFO [
	^ typeFlag = $6
]

{ #category : #testing }
PhaNAPITarArchiveMember >> isFile [
	^ typeFlag = $0 or: [ typeFlag = Character null ]
]

{ #category : #testing }
PhaNAPITarArchiveMember >> isHardLink [
	^ typeFlag = $1
]

{ #category : #testing }
PhaNAPITarArchiveMember >> isSymbolicLink [
	^ typeFlag = $2
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> lastModificationTime [
	^ lastModificationTime
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> lastModificationTime: anObject [
	lastModificationTime := anObject
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> linkedFileName [
	^ linkedFileName
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> linkedFileName: anObject [
	linkedFileName := anObject
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> ownerGroupName [
	^ ownerGroupName
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> ownerGroupName: anObject [
	ownerGroupName := anObject
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> ownerUserID [
	^ ownerUserID
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> ownerUserID: anObject [
	ownerUserID := anObject
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> ownerUserName [
	^ ownerUserName
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> ownerUserName: anObject [
	ownerUserName := anObject
]

{ #category : #'initialize-release' }
PhaNAPITarArchiveMember >> readContentFrom: stream [
	| paddedSize paddingSize |
	content := stream next: fileSize.
	paddedSize := fileSize alignedTo: 512.
	paddingSize := paddedSize - fileSize.
	stream skip: paddingSize
]

{ #category : #'initialize-release' }
PhaNAPITarArchiveMember >> readFrom: in integerWithSize: stringSize [
	^ (in next: stringSize) asString asInteger
]

{ #category : #'initialize-release' }
PhaNAPITarArchiveMember >> readFrom: in octalWithSize: stringSize [
	^ Integer readFrom: (in next: stringSize) asString base: 8
]

{ #category : #'initialize-release' }
PhaNAPITarArchiveMember >> readFrom: in stringWithSize: stringSize [
	| rawBytes nullIndex bytes |
	rawBytes := in next: stringSize.
	nullIndex := rawBytes indexOf: 0.
	bytes := nullIndex = 0
		ifTrue: [rawBytes]
		ifFalse: [ rawBytes first: nullIndex - 1 ].
	^ bytes utf8Decoded
]

{ #category : #'initialize-release' }
PhaNAPITarArchiveMember >> readHeaderFrom: recordData [
	| in headerRecordChecksum ustar ustarVersion |
	in := ReadStream on: recordData.
	fileName := self readFrom: in stringWithSize: 100.
	fileMode := self readFrom: in octalWithSize: 8.
	ownerUserID := self readFrom: in integerWithSize: 8.
	groupID := self readFrom: in integerWithSize: 8.
	fileSize := self readFrom: in octalWithSize: 12.
	lastModificationTime := self readFrom: in octalWithSize: 12.
	headerRecordChecksum := self readFrom: in stringWithSize: 8.
	typeFlag := in next asCharacter.
	linkedFileName := self readFrom: in stringWithSize: 100.
	ustar := self readFrom: in stringWithSize: 6.
	(ustar beginsWith: 'ustar') ifTrue: [ 
		ustarVersion := self readFrom: in stringWithSize: 2.
		ownerUserName := self readFrom: in stringWithSize: 32.
		ownerGroupName := self readFrom: in stringWithSize: 32.
		deviceMajorNumber := self readFrom: in integerWithSize: 8.
		deviceMinorNumber := self readFrom: in integerWithSize: 8.
		fileName := (self readFrom: in stringWithSize: 155) , fileName.
	]
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> typeFlag [
	^ typeFlag
]

{ #category : #accessing }
PhaNAPITarArchiveMember >> typeFlag: anObject [
	typeFlag := anObject
]
