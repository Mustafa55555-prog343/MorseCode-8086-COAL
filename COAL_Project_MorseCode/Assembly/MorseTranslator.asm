; =============================================================================
;  MORSE CODE COMMUNICATION AND EMERGENCY SIGNALING SYSTEM
;  End-of-Semester Project  |  CS-234: Computer Organization & Assembly Language
;  Author : Mustafa Shahid   |   Class  : BSCS-14B   |   CMS ID : 500889
;  Target : x86 (16-bit)     |   Tool   : emu8086 / MASM / TASM
; -----------------------------------------------------------------------------
;  COAL CONCEPTS DEMONSTRATED:
;     * Instruction Set Architecture (8086)
;     * Data Definition Directives (DB, DW, EQU)
;     * Direct Addressing Mode          (MOV AL, [name])
;     * Indirect Addressing Mode        (MOV AL, [BX])
;     * Indexed Addressing Mode         (MOV AL, [SI + offset])
;     * Base-plus-Offset Addressing     (MOV AL, [BX + SI])
;     * Arithmetic & Logical Operations (ADD, SUB, AND, OR, CMP)
;     * BIOS / DOS Software Interrupts  (INT 21h, INT 10h, INT 16h)
;     * I/O Port Operations             (PC-speaker beep)
;     * Interrupt Vector Table usage    (INT 21h service routing)
; =============================================================================

.MODEL SMALL                        ; small memory model (64K code + 64K data)
.STACK 100h                         ; reserve 256 bytes for the stack

; -----------------------------------------------------------------------------
;                              DATA SEGMENT
; -----------------------------------------------------------------------------
.DATA

    ; ---- User-interface prompts (null-terminated with '$' for INT 21h/09h) ----
    welcome_msg     DB 0DH,0AH,'======================================',0DH,0AH
                    DB '  MORSE CODE TRANSLATOR  -  BSCS-14B  ',0DH,0AH
                    DB '     Author : Mustafa Shahid          ',0DH,0AH
                    DB '     CMS ID : 500889                  ',0DH,0AH
                    DB '======================================',0DH,0AH,'$'

    prompt_input    DB 0DH,0AH,'Enter text to translate (A-Z, 0-9, max 60): ',
                    DB '$'

    prompt_output   DB 0DH,0AH,'Morse Code Output :',0DH,0AH,'$'
    prompt_sos      DB 0DH,0AH,'Emergency SOS signal fired on PC speaker!',
                    DB 0DH,0AH,'$'
    newline         DB 0DH,0AH,'$'
    space_morse     DB '   ','$'    ; three spaces between Morse words

    ; ---- Buffer for user keyboard input (DOS service 0Ah needs this layout) ----
    input_buffer    DB 62              ; max characters (60 + CR + safety)
                    DB ?               ; actual length (filled by DOS)
                    DB 62 DUP('$')     ; character storage

    ; ============  MORSE LOOKUP TABLE  ============
    ; Each entry is exactly 6 bytes:
    ;     byte 0..4 : Morse symbols ('.' and '-'), padded with spaces
    ;     byte 5    : length of the Morse code (1-5)
    ; This fixed-size record layout lets us use INDEXED ADDRESSING:
    ;     address = base + (char_index * 6)
    ; --------------------------------------------------

    ; ---- Letters A-Z (entries 0..25) ----
    morse_table     DB '.-   ',1        ; A
                    DB '-... ',4        ; B
                    DB '-.-. ',4        ; C
                    DB '-..  ',3        ; D
                    DB '.    ',1        ; E
                    DB '..-. ',4        ; F
                    DB '--.  ',3        ; G
                    DB '.... ',4        ; H
                    DB '..   ',2        ; I
                    DB '.--- ',4        ; J
                    DB '-.-  ',3        ; K
                    DB '.-.. ',4        ; L
                    DB '--   ',2        ; M
                    DB '-.   ',2        ; N
                    DB '---  ',3        ; O
                    DB '.--. ',4        ; P
                    DB '--.- ',4        ; Q
                    DB '.-.  ',3        ; R
                    DB '...  ',3        ; S
                    DB '-    ',1        ; T
                    DB '..-  ',3        ; U
                    DB '...- ',4        ; V
                    DB '.--  ',3        ; W
                    DB '-..- ',4        ; X
                    DB '-.-- ',4        ; Y
                    DB '--.. ',4        ; Z

    ; ---- Digits 0-9 (entries 26..35) ----
                    DB '-----',5        ; 0
                    DB '.----',5        ; 1
                    DB '..---',5        ; 2
                    DB '...--',5        ; 3
                    DB '....-',5        ; 4
                    DB '.....',5        ; 5
                    DB '-....',5        ; 6
                    DB '--...',5        ; 7
                    DB '---..',5        ; 8
                    DB '----.',5        ; 9

    RECORD_SIZE     EQU 6               ; size in bytes of one lookup entry

    ; ---- "S O S" encoded once (three dots, three dashes, three dots) -----
    sos_pattern     DB '...---...$'

; -----------------------------------------------------------------------------
;                              CODE SEGMENT
; -----------------------------------------------------------------------------
.CODE

MAIN PROC
    ; ---- Initialize DS register with the address of the data segment ----
    MOV  AX, @DATA                   ; load address of DATA into AX
    MOV  DS, AX                      ; move it into DS (segment register)

    ; ---- Print welcome banner (DOS function 09h = print $-terminated str) ----
    LEA  DX, welcome_msg             ; DX <- offset of banner text
    MOV  AH, 09h                     ; AH = 09h : display string service
    INT  21h                         ; DOS software interrupt

    ; ---- Ask the user for input text ----
    LEA  DX, prompt_input            ; load prompt address
    MOV  AH, 09h                     ; display-string service
    INT  21h                         ; call DOS interrupt

    ; ---- Read buffered input (DOS function 0Ah) ----
    LEA  DX, input_buffer            ; DX points to buffer header
    MOV  AH, 0Ah                     ; buffered keyboard input
    INT  21h                         ; DOS interrupt handles keystrokes

    ; ---- Print "Morse Code Output:" header ----
    LEA  DX, prompt_output           ; load offset of header
    MOV  AH, 09h                     ; print string
    INT  21h                         ; DOS service

    ; ---- Prepare pointers for translation loop ----
    LEA  SI, input_buffer + 2        ; SI -> first user character
    MOV  CL, [input_buffer + 1]      ; CL = number of chars user entered
    XOR  CH, CH                      ; clear high byte (CX = full count)
    MOV  BX, OFFSET morse_table      ; BX = base address of lookup table

TRANSLATE_LOOP:
    CMP  CX, 0                       ; have we processed all chars?
    JE   AFTER_TRANSLATE             ; yes -> exit loop

    MOV  AL, [SI]                    ; AL = current character (indirect mode)

    ; ---- Convert lowercase to uppercase (logical AND with 11011111b) ----
    CMP  AL, 'a'                     ; is it >= 'a' ?
    JB   CHECK_SPACE                 ; no, skip conversion
    CMP  AL, 'z'                     ; is it <= 'z' ?
    JA   CHECK_SPACE                 ; no, skip conversion
    AND  AL, 0DFh                    ; clear bit-5 -> uppercase

CHECK_SPACE:
    CMP  AL, ' '                     ; word separator?
    JNE  CHECK_DIGIT                 ; no -> test next category
    LEA  DX, space_morse             ; yes -> print "   "
    MOV  AH, 09h
    INT  21h
    JMP  NEXT_CHAR                   ; skip to next character

CHECK_DIGIT:
    CMP  AL, '0'                     ; below '0' -> unsupported
    JB   NEXT_CHAR
    CMP  AL, '9'                     ; between '0' and '9' ?
    JA   CHECK_LETTER                ; no, test letters
    SUB  AL, '0'                     ; digit index (0..9)
    ADD  AL, 26                      ; digits start at slot 26
    JMP  PRINT_CODE

CHECK_LETTER:
    CMP  AL, 'A'                     ; below 'A' -> ignore
    JB   NEXT_CHAR
    CMP  AL, 'Z'                     ; above 'Z' -> ignore
    JA   NEXT_CHAR
    SUB  AL, 'A'                     ; letter index 0..25

PRINT_CODE:
    ; ---- Compute address of Morse entry: base + index*RECORD_SIZE -------
    MOV  AH, 0                       ; clear AH for multiplication
    MOV  DL, RECORD_SIZE             ; DL = 6
    MUL  DL                          ; AX = index * 6
    MOV  DI, AX                      ; DI = offset inside table

    ; ---- Read length byte using BASE+INDEX+DISPLACEMENT addressing -------
    MOV  CH, [BX + DI + 5]           ; CH = number of dots/dashes

    ; ---- Print each symbol character one-by-one via DOS function 02h -----
    XOR  AH, AH                      ; zero AH
PRINT_SYMBOL:
    CMP  CH, 0                       ; all symbols printed?
    JE   PRINT_SPACER
    MOV  DL, [BX + DI]               ; load current symbol (indexed mode)
    PUSH AX                          ; save AX
    PUSH CX                          ; save loop counters
    MOV  AH, 02h                     ; DOS function: display character
    INT  21h                         ; output dot or dash
    POP  CX
    POP  AX
    INC  DI                          ; advance pointer to next symbol
    DEC  CH                          ; one fewer symbol remaining
    JMP  PRINT_SYMBOL

PRINT_SPACER:
    MOV  DL, ' '                     ; one-space gap between letters
    MOV  AH, 02h                     ; DOS: display char
    INT  21h                         ; call

NEXT_CHAR:
    INC  SI                          ; move to next input character
    DEC  CX                          ; one fewer char to process
    JMP  TRANSLATE_LOOP              ; continue translating

AFTER_TRANSLATE:
    ; ---- Fire audible SOS signal on the PC speaker as emergency demo ----
    LEA  DX, prompt_sos              ; banner
    MOV  AH, 09h
    INT  21h

    CALL PLAY_SOS                    ; invoke speaker-beep subroutine

    ; ---- Terminate program cleanly (DOS function 4Ch) -------------------
    MOV  AH, 4Ch                     ; DOS : terminate with return code
    MOV  AL, 00h                     ; exit code 0 (success)
    INT  21h                         ; transfer control back to DOS
MAIN ENDP


; =============================================================================
;  PLAY_SOS : audibly transmit "... --- ..." via BIOS/speaker
;  Uses INT 21h service 02h to emit ASCII-7 (BEL) for a short audible click
;  and a delay loop between signals.
; =============================================================================
PLAY_SOS PROC
    MOV  CX, 3                       ; three dots
SOS_DOT1:
    CALL BEEP_SHORT
    LOOP SOS_DOT1

    CALL GAP                         ; inter-letter gap

    MOV  CX, 3                       ; three dashes
SOS_DASH:
    CALL BEEP_LONG
    LOOP SOS_DASH

    CALL GAP                         ; inter-letter gap

    MOV  CX, 3                       ; three dots
SOS_DOT2:
    CALL BEEP_SHORT
    LOOP SOS_DOT2

    RET
PLAY_SOS ENDP


; --- BEEP_SHORT : dot -------------------------------------------------------
BEEP_SHORT PROC
    PUSH AX
    PUSH DX
    MOV  DL, 07h                     ; ASCII BEL character
    MOV  AH, 02h                     ; DOS display-char
    INT  21h                         ; play short beep
    CALL SHORT_DELAY
    POP  DX
    POP  AX
    RET
BEEP_SHORT ENDP

; --- BEEP_LONG : dash (3x length) ------------------------------------------
BEEP_LONG PROC
    PUSH AX
    PUSH DX
    MOV  DL, 07h                     ; BEL character
    MOV  AH, 02h                     ; DOS display-char
    INT  21h
    CALL LONG_DELAY
    POP  DX
    POP  AX
    RET
BEEP_LONG ENDP

; --- GAP : silent pause between letters ------------------------------------
GAP PROC
    PUSH CX
    MOV  CX, 0FFFFh                  ; outer loop
GAP_LOOP:
    NOP
    LOOP GAP_LOOP
    POP  CX
    RET
GAP ENDP

; --- SHORT_DELAY : tiny software-timed pause -------------------------------
SHORT_DELAY PROC
    PUSH CX
    MOV  CX, 07FFFh
SD_L:
    NOP
    LOOP SD_L
    POP  CX
    RET
SHORT_DELAY ENDP

; --- LONG_DELAY : 3x longer pause ------------------------------------------
LONG_DELAY PROC
    PUSH CX
    PUSH DX
    MOV  DX, 3
LD_OUTER:
    MOV  CX, 0FFFFh
LD_INNER:
    NOP
    LOOP LD_INNER
    DEC  DX
    JNZ  LD_OUTER
    POP  DX
    POP  CX
    RET
LONG_DELAY ENDP

END MAIN                             ; end of program, entry point = MAIN
