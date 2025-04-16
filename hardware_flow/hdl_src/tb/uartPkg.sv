/*********************************************/
// Author           :   Andrea Galimberti (andrea.galimberti@polimi.it),
//                      Davide Galli (davide.galli@polimi.it),
//                      Davide Zoni (davide.zoni@polimi.it)
//
// Description      :
//
/*********************************************/

package uartPkg;

// BaudRate 1.000.000 bit/s @ 50MHz

    // Set in the uart ctrl at init stage: clk/(16*1.000.000)
    localparam UART_CLK_DIV_DEF             = 8'd3; 
    // Set in the testbench depending on the running frequency of the simulation  
    localparam SIM_HALF_CLK_PERIOD_DEF      = 10;
    // Set in the testbench depending on the running frequency of the simulation: clk / (baud_rate) 
    localparam SIM_UART_NUM_CLK_TICKS_BIT   = 50;
	
	
// BaudRate 115200 bit/s @ 50MHz
    
    // Set in the uart ctrl at init stage: clk/(16*1.000.000)
    //localparam UART_CLK_DIV_DEF           = 8'd27; 
    // Set in the testbench depending on the running frequency of the simulation  
    //localparam SIM_HALF_CLK_PERIOD_DEF    = 10;
    // Set in the testbench depending on the running frequency of the simulation: clk / (baud_rate) 
    //localparam SIM_UART_NUM_CLK_TICKS_BIT = 434;

// ******************************************************************************

    // Register addresses
    localparam UART_REG_RB  = 3'd0;   // receiver buffer
    localparam UART_REG_TR  = 3'd0;   // transmitter
    localparam UART_REG_IE  = 3'd1;   // Interrupt enable
    localparam UART_REG_II  = 3'd2;   // Interrupt identification
    localparam UART_REG_FC  = 3'd2;   // FIFO control
    localparam UART_REG_LC  = 3'd3;   // Line Control
    localparam UART_REG_MC  = 3'd4;   // Modem control
    localparam UART_REG_LS  = 3'd5;   // Line status
    localparam UART_REG_MS  = 3'd6;   // Modem status
    localparam UART_REG_SR  = 3'd7;   // Scratch register
    localparam UART_REG_DL1 = 3'd0;   // Divisor latch bytes (1-2)
    localparam UART_REG_DL2 = 3'd1;

    // Interrupt Enable register bits
    localparam UART_IE_RDA	=  0;	// Received Data available interrupt
    localparam UART_IE_THRE =  1;	// Transmitter Holding Register empty interrupt
    localparam UART_IE_RLS	=  2;	// Receiver Line Status Interrupt
    localparam UART_IE_MS	=  3;	// Modem Status Interrupt

    // Interrupt Identification register bits
    localparam UART_II_IP	= 0;	    // Interrupt pending when 0
    localparam UART_II_II_B	= 3; 	// Interrupt identification
    localparam UART_II_II_E	= 1; 	// Interrupt identification

    // Interrupt identification values for bits 3:1
    localparam UART_II_RLS	= 3'b011;	// Receiver Line Status
    localparam UART_II_RDA	= 3'b010;	// Receiver Data available
    localparam UART_II_TI	= 3'b110;	// Timeout Indication
    localparam UART_II_THRE	= 3'b001;	// Transmitter Holding Register empty
    localparam UART_II_MS	= 3'b000;	// Modem Status

    // FIFO Control Register bits
    localparam UART_FC_TL_B	= 1;	// Trigger level
    localparam UART_FC_TL_E	= 0;	// Trigger level

    // FIFO trigger level values
    localparam UART_FC_1	= 2'b00;
    localparam UART_FC_4	= 2'b01;
    localparam UART_FC_8	= 2'b10;
    localparam UART_FC_14	= 2'b11;

    // Line Control register bits
    //localparam UART_LC_BITS	= 1:0	// bits in character
    localparam UART_LC_SB	= 2;	// stop bits
    localparam UART_LC_PE	= 3;	// parity enable
    localparam UART_LC_EP	= 4;	// even parity
    localparam UART_LC_SP	= 5;	// stick parity
    localparam UART_LC_BC	= 6;	// Break control
    localparam UART_LC_DL	= 7;	// Divisor Latch access bit

    // Modem Control register bits
    localparam UART_MC_DTR	= 0;
    localparam UART_MC_RTS	= 1;
    localparam UART_MC_OUT1	= 2;
    localparam UART_MC_OUT2	= 3;
    localparam UART_MC_LB	= 4; // Loopback mode

    // Line Status Register bits
    localparam UART_LS_DR	= 0;	// Data ready
    localparam UART_LS_OE	= 1;	// Overrun Error
    localparam UART_LS_PE	= 2;	// Parity Error
    localparam UART_LS_FE	= 3;	// Framing Error
    localparam UART_LS_BI	= 4;	// Break interrupt
    localparam UART_LS_TFE	= 5;	// Transmit FIFO is empty
    localparam UART_LS_TE	= 6;	// Transmitter Empty indicator
    localparam UART_LS_EI	= 7;	// Error indicator

    // Modem Status Register bits
    localparam UART_MS_DCTS	= 0;	// Delta signals
    localparam UART_MS_DDSR	= 1;
    localparam UART_MS_TERI	= 2;
    localparam UART_MS_DDCD	= 3;
    localparam UART_MS_CCTS	= 4;	// Complement signals
    localparam UART_MS_CDSR	= 5;
    localparam UART_MS_CRI	= 6;
    localparam UART_MS_CDCD	= 7;

    // FIFO parameter defines

    localparam UART_FIFO_WIDTH	    = 8;
    localparam UART_FIFO_DEPTH	    = 16;
    localparam UART_FIFO_POINTER_W	= 4;
    localparam UART_FIFO_COUNTER_W	= 5;
    // receiver fifo has width 11 because it has break, parity and framing error bits
    localparam UART_FIFO_REC_WIDTH  = 11;

endpackage